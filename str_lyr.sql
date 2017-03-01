ALTER TABLE tmp.street_cnt_line ADD COLUMN widthright integer DEFAULT 0; -- dynamic corner offset
ALTER TABLE tmp.street_cnt_line ADD COLUMN widthleft integer DEFAULT 0; -- dynamic corner offset

-- make equal parity street side each other's opposite
UPDATE tmp.street_cnt_line SET fromleft = -2, toleft = -2 WHERE fromleft = -1 AND fromright % 2 = 1;
UPDATE tmp.street_cnt_line SET fromright = -2, toright = -2 WHERE fromright = -1 AND fromleft % 2 = 1;

-- consider mixed parity streets (squares) differently
-- odd house numbers will be shifted 'downward'
-- even house numbers will be shifted 'upward'
-- to eliminate collision
UPDATE tmp.street_cnt_line d SET fromleft = -3, toleft = -3 FROM (SELECT s.gid as xgid
FROM tmp.street_cnt_line c, tmp.street_cnt_line s WHERE c.fromleft = -2 AND c.street = s.street AND ST_Intersects(c.geom, s.geom)) w WHERE d.fromleft = -1 AND d.gid = w.xgid;

UPDATE tmp.street_cnt_line d SET fromright = -3, toright = -3 FROM (SELECT s.gid as xgid
FROM tmp.street_cnt_line c, tmp.street_cnt_line s WHERE c.fromright = -2 AND c.street = s.street AND ST_Intersects(c.geom, s.geom)) w WHERE d.fromright = -1 AND d.gid = w.xgid;

UPDATE tmp.street_cnt_line d SET fromleft = -4, toleft = -4 FROM (SELECT s.gid as xgid
FROM tmp.street_cnt_line c, tmp.street_cnt_line s WHERE c.fromleft = -3 AND c.street = s.street AND ST_Intersects(c.geom, s.geom)) w WHERE d.fromleft = -2 AND d.gid = w.xgid;

UPDATE tmp.street_cnt_line d SET fromright = -4, toright = -4 FROM (SELECT s.gid as xgid
FROM tmp.street_cnt_line c, tmp.street_cnt_line s WHERE c.fromright = -3 AND c.street = s.street AND ST_Intersects(c.geom, s.geom)) w WHERE d.fromright = -2 AND d.gid = w.xgid;

-- dynamic corner offset on mixed parity streets (squares)
UPDATE tmp.street_cnt_line SET widthleft = abs(ln(ST_Length(ST_LineMerge(geom))/10.0))/3.0*ST_Length(ST_LineMerge(geom))/GREATEST((toleft-fromleft)::float,1.0)/2.0 WHERE toleft < -2  OR toright < -2 ;
UPDATE tmp.street_cnt_line SET widthright = abs(ln(ST_Length(ST_LineMerge(geom))/10.0))/3.0*ST_Length(ST_LineMerge(geom))/GREATEST((toright-fromright)::float,1.0)/2.0 WHERE toright < -2 OR toleft < -2;

-- dynamic corner offset on the rest
UPDATE tmp.street_cnt_line SET widthleft = abs(ln(ST_Length(ST_LineMerge(geom))/10.0))/3.0*ST_Length(ST_LineMerge(geom))/GREATEST((toleft-fromleft)::float,1.0) WHERE toleft > 0 AND widthleft = 0 ;
UPDATE tmp.street_cnt_line SET widthright = abs(ln(ST_Length(ST_LineMerge(geom))/10.0))/3.0*ST_Length(ST_LineMerge(geom))/GREATEST((toright-fromright)::float,1.0) WHERE toright > 0 AND widthright = 0;
