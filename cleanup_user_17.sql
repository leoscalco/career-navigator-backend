-- Clean all data for user_id = 17
-- This script deletes all related records and then the user record itself

BEGIN;

-- Delete generated products
DELETE FROM generated_products WHERE user_id = 17;

-- Delete academic records
DELETE FROM academic_records WHERE user_id = 17;

-- Delete courses
DELETE FROM courses WHERE user_id = 17;

-- Delete job experiences
DELETE FROM job_experiences WHERE user_id = 17;

-- Delete user profile
DELETE FROM user_profiles WHERE user_id = 17;

-- Finally, delete the user
DELETE FROM users WHERE id = 17;

COMMIT;

-- Verify deletion (optional - uncomment to check)
-- SELECT COUNT(*) FROM users WHERE id = 17;
-- SELECT COUNT(*) FROM user_profiles WHERE user_id = 17;
-- SELECT COUNT(*) FROM job_experiences WHERE user_id = 17;
-- SELECT COUNT(*) FROM courses WHERE user_id = 17;
-- SELECT COUNT(*) FROM academic_records WHERE user_id = 17;
-- SELECT COUNT(*) FROM generated_products WHERE user_id = 17;

