-- Classify every person in two snapshots of staff_observations.
-- Parameters: :prev_snapshot, :curr_snapshot
--
-- change_type: unchanged | position_change | likely_transfer | possible_transfer |
--              departure | addition | status_unknown
-- confidence:  high | medium | low. Low-confidence links are reported but never merged:
--              the person also still shows up as a departure and an addition.
WITH
prev AS (
    SELECT * FROM staff_observations WHERE snapshot_id = :prev_snapshot
),
curr AS (
    SELECT * FROM staff_observations WHERE snapshot_id = :curr_snapshot
),
covered AS (
    SELECT school_id FROM snapshot_coverage WHERE snapshot_id = :curr_snapshot
),

-- 1. Same school: match on email first, then on exact normalized name.
match_candidates AS (
    SELECT
        p.observation_id AS prev_obs,
        c.observation_id AS curr_obs,
        CASE WHEN p.email = c.email THEN 'email' ELSE 'name' END AS match_basis
    FROM prev AS p
    JOIN curr AS c
        ON p.school_id = c.school_id
        AND (p.email = c.email OR p.name_key = c.name_key)
),
-- Each record is used at most once, email matches win over name matches.
ranked_matches AS (
    SELECT
        *,
        row_number() OVER (
            PARTITION BY prev_obs ORDER BY match_basis = 'email' DESC, curr_obs
        ) AS prev_rank,
        row_number() OVER (
            PARTITION BY curr_obs ORDER BY match_basis = 'email' DESC, prev_obs
        ) AS curr_rank
    FROM match_candidates
),
matches AS (
    SELECT prev_obs, curr_obs, match_basis
    FROM ranked_matches
    WHERE prev_rank = 1 AND curr_rank = 1
),
unmatched_prev AS (
    SELECT * FROM prev WHERE observation_id NOT IN (SELECT prev_obs FROM matches)
),
unmatched_curr AS (
    SELECT * FROM curr WHERE observation_id NOT IN (SELECT curr_obs FROM matches)
),

-- 2. Different school, same name. A name alone is weak evidence (common names collide),
--    so it needs a corroborating contact detail to reach 'medium'.
transfer_candidates AS (
    SELECT
        p.observation_id AS prev_obs,
        c.observation_id AS curr_obs,
        'same name'
            || CASE WHEN p.phone = c.phone THEN ', same phone' ELSE '' END
            || CASE WHEN p.email = c.email THEN ', same email' ELSE '' END
            || CASE
                WHEN p.email <> c.email
                    AND substr(p.email, 1, instr(p.email, '@') - 1)
                        = substr(c.email, 1, instr(c.email, '@') - 1)
                THEN ', same email username'
                ELSE ''
            END AS evidence
    FROM unmatched_prev AS p
    JOIN unmatched_curr AS c
        ON p.name_key = c.name_key
        AND p.school_id <> c.school_id
),
transfers AS (
    SELECT
        *,
        CASE WHEN evidence = 'same name' THEN 'low' ELSE 'medium' END AS confidence
    FROM transfer_candidates
),
linked_prev AS (SELECT prev_obs FROM transfers WHERE confidence = 'medium'),
linked_curr AS (SELECT curr_obs FROM transfers WHERE confidence = 'medium')

SELECT
    CASE
        WHEN lower(p.title) IS lower(c.title) THEN 'unchanged'
        ELSE 'position_change'
    END AS change_type,
    CASE m.match_basis WHEN 'email' THEN 'high' ELSE 'medium' END AS confidence,
    p.staff_id,
    c.name,
    p.school_id AS prev_school_id,
    c.school_id AS curr_school_id,
    p.title AS prev_title,
    c.title AS curr_title,
    'same school, matched on ' || m.match_basis AS evidence
FROM matches AS m
JOIN prev AS p ON p.observation_id = m.prev_obs
JOIN curr AS c ON c.observation_id = m.curr_obs

UNION ALL

SELECT
    CASE t.confidence WHEN 'medium' THEN 'likely_transfer' ELSE 'possible_transfer' END,
    t.confidence,
    p.staff_id,
    c.name,
    p.school_id,
    c.school_id,
    p.title,
    c.title,
    t.evidence
FROM transfers AS t
JOIN prev AS p ON p.observation_id = t.prev_obs
JOIN curr AS c ON c.observation_id = t.curr_obs

UNION ALL

-- Absent from one scrape could still be scrape noise, hence 'medium'.
SELECT
    CASE WHEN p.school_id IN (SELECT school_id FROM covered) THEN 'departure' ELSE 'status_unknown' END,
    CASE WHEN p.school_id IN (SELECT school_id FROM covered) THEN 'medium' END,
    p.staff_id,
    p.name,
    p.school_id,
    NULL,
    p.title,
    NULL,
    CASE
        WHEN p.school_id IN (SELECT school_id FROM covered) THEN 'not on current school page'
        ELSE 'school not scraped in current snapshot'
    END
FROM unmatched_prev AS p
WHERE p.observation_id NOT IN (SELECT prev_obs FROM linked_prev)

UNION ALL

SELECT
    'addition',
    CASE WHEN c.email IS NULL THEN 'medium' ELSE 'high' END,
    NULL,
    c.name,
    NULL,
    c.school_id,
    NULL,
    c.title,
    CASE
        WHEN c.email IS NULL THEN 'not in previous snapshot; no email to confirm identity'
        ELSE 'not in previous snapshot'
    END
FROM unmatched_curr AS c
WHERE c.observation_id NOT IN (SELECT curr_obs FROM linked_curr)

ORDER BY change_type, name
