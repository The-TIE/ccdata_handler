-- Get exchanges rated 'BB' or better
SELECT internal_name
FROM market.cc_exchanges_general
WHERE grade IN ('AAA', 'AA', 'A', 'BBB', 'BB');