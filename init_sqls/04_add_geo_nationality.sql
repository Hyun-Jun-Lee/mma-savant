-- event: 위도/경도 추가
ALTER TABLE event ADD COLUMN IF NOT EXISTS latitude FLOAT;
ALTER TABLE event ADD COLUMN IF NOT EXISTS longitude FLOAT;

-- fighter: 국적 추가
ALTER TABLE fighter ADD COLUMN IF NOT EXISTS nationality VARCHAR;
