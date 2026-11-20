-- Additive foundation only. Run in an isolated schema first; live activation is a separate rollout.
CREATE TABLE IF NOT EXISTS de_students (
  id CHAR(36) CHARACTER SET ascii PRIMARY KEY,
  status ENUM('active','guardian_pending','disabled') NOT NULL DEFAULT 'guardian_pending',
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  INDEX student_created (created_at,id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_contacts (
  student_id CHAR(36) CHARACTER SET ascii PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(254) NOT NULL,
  mobile VARCHAR(20) NOT NULL,
  saved_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  FOREIGN KEY (student_id) REFERENCES de_students(id)
) ENGINE=InnoDB;

-- Only verified provider subjects enter this table. Typed contacts cannot own an identity.
CREATE TABLE IF NOT EXISTS de_identities (
  provider ENUM('google','phone','apple') NOT NULL,
  subject VARCHAR(255) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  student_id CHAR(36) CHARACTER SET ascii NOT NULL,
  verified_at DATETIME(3) NOT NULL,
  PRIMARY KEY(provider,subject),
  INDEX identity_student(student_id),
  FOREIGN KEY (student_id) REFERENCES de_students(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_education (
  student_id CHAR(36) CHARACTER SET ascii PRIMARY KEY,
  level ENUM('10','11','12','graduation','masters') NOT NULL,
  state VARCHAR(80) NOT NULL,
  city VARCHAR(100) NOT NULL,
  saved_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  FOREIGN KEY (student_id) REFERENCES de_students(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_preferences (
  student_id CHAR(36) CHARACTER SET ascii PRIMARY KEY,
  dob DATE NULL,
  report_email BOOLEAN NOT NULL DEFAULT FALSE,
  birthday_completed BOOLEAN NOT NULL DEFAULT FALSE,
  saved_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  FOREIGN KEY (student_id) REFERENCES de_students(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_consents (
  id CHAR(36) CHARACTER SET ascii PRIMARY KEY,
  student_id CHAR(36) CHARACTER SET ascii NOT NULL,
  purpose ENUM('account','guardian','report_email','school_report') NOT NULL,
  policy_version VARCHAR(32) NOT NULL,
  proof_reference VARCHAR(255) NULL,
  granted_at DATETIME(3) NOT NULL,
  revoked_at DATETIME(3) NULL,
  INDEX consent_student(student_id,purpose,granted_at),
  FOREIGN KEY (student_id) REFERENCES de_students(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_sessions (
  token_hash BINARY(32) PRIMARY KEY,
  student_id CHAR(36) CHARACTER SET ascii NOT NULL,
  client ENUM('web','ios','android') NOT NULL,
  expires_at DATETIME(3) NOT NULL,
  revoked_at DATETIME(3) NULL,
  INDEX session_expiry(expires_at),
  INDEX session_student(student_id),
  FOREIGN KEY (student_id) REFERENCES de_students(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_schools (
  id CHAR(36) CHARACTER SET ascii PRIMARY KEY,
  name VARCHAR(180) NOT NULL,
  state VARCHAR(80) NOT NULL,
  city VARCHAR(100) NOT NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_coupons (
  id CHAR(36) CHARACTER SET ascii PRIMARY KEY,
  code_hash BINARY(32) NOT NULL UNIQUE,
  kind ENUM('welcome','comeback','school') NOT NULL,
  school_id CHAR(36) CHARACTER SET ascii NULL,
  exam VARCHAR(50) CHARACTER SET ascii NULL,
  active BOOLEAN NOT NULL DEFAULT TRUE,
  starts_at DATETIME(3) NOT NULL,
  expires_at DATETIME(3) NOT NULL,
  redemption_limit INT UNSIGNED NOT NULL,
  used INT UNSIGNED NOT NULL DEFAULT 0,
  CHECK (used <= redemption_limit),
  CHECK (redemption_limit > 0),
  CHECK (expires_at > starts_at),
  CHECK ((kind = 'school' AND school_id IS NOT NULL) OR (kind <> 'school' AND school_id IS NULL)),
  FOREIGN KEY (school_id) REFERENCES de_schools(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_orders (
  id CHAR(36) CHARACTER SET ascii PRIMARY KEY,
  student_id CHAR(36) CHARACTER SET ascii NOT NULL,
  test_id VARCHAR(120) CHARACTER SET ascii NOT NULL,
  idempotency_key VARCHAR(80) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
  coupon_id CHAR(36) CHARACTER SET ascii NULL,
  product ENUM('monthly','single') NOT NULL DEFAULT 'single',
  price_paise INT UNSIGNED NOT NULL,
  discount_paise INT UNSIGNED NOT NULL,
  due_paise INT UNSIGNED NOT NULL,
  currency CHAR(3) CHARACTER SET ascii NOT NULL DEFAULT 'INR',
  status ENUM('pending','paid','void','refunded') NOT NULL,
  gateway_order VARCHAR(120) CHARACTER SET ascii NULL UNIQUE,
  gateway_payment VARCHAR(120) CHARACTER SET ascii NULL UNIQUE,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  UNIQUE order_retry(student_id,idempotency_key),
  INDEX order_student(student_id,created_at,id),
  CHECK (due_paise + discount_paise = price_paise),
  CHECK (currency = 'INR'),
  FOREIGN KEY (student_id) REFERENCES de_students(id),
  FOREIGN KEY (coupon_id) REFERENCES de_coupons(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_redemptions (
  coupon_id CHAR(36) CHARACTER SET ascii NOT NULL,
  student_id CHAR(36) CHARACTER SET ascii NOT NULL,
  order_id CHAR(36) CHARACTER SET ascii NOT NULL UNIQUE,
  PRIMARY KEY(coupon_id,student_id),
  FOREIGN KEY (coupon_id) REFERENCES de_coupons(id),
  FOREIGN KEY (student_id) REFERENCES de_students(id),
  FOREIGN KEY (order_id) REFERENCES de_orders(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_entitlements (
  id CHAR(36) CHARACTER SET ascii PRIMARY KEY,
  order_id CHAR(36) CHARACTER SET ascii NOT NULL UNIQUE,
  student_id CHAR(36) CHARACTER SET ascii NOT NULL,
  test_id VARCHAR(120) CHARACTER SET ascii NOT NULL,
  revoked_at DATETIME(3) NULL,
  INDEX entitlement_student(student_id),
  FOREIGN KEY (order_id) REFERENCES de_orders(id),
  FOREIGN KEY (student_id) REFERENCES de_students(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_monthly_passes (
  id CHAR(36) CHARACTER SET ascii PRIMARY KEY,
  order_id CHAR(36) CHARACTER SET ascii NOT NULL UNIQUE,
  student_id CHAR(36) CHARACTER SET ascii NOT NULL,
  starts_at DATETIME(3) NOT NULL,
  expires_at DATETIME(3) NOT NULL,
  revoked_at DATETIME(3) NULL,
  CHECK (expires_at > starts_at),
  INDEX pass_student(student_id,expires_at),
  FOREIGN KEY (order_id) REFERENCES de_orders(id),
  FOREIGN KEY (student_id) REFERENCES de_students(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_attempts (
  id CHAR(36) CHARACTER SET ascii PRIMARY KEY,
  entitlement_id CHAR(36) CHARACTER SET ascii NULL UNIQUE,
  monthly_pass_id CHAR(36) CHARACTER SET ascii NULL,
  student_id CHAR(36) CHARACTER SET ascii NOT NULL,
  snapshot_key VARCHAR(255) CHARACTER SET ascii NOT NULL,
  snapshot_sha BINARY(32) NOT NULL,
  state ENUM('active','submitted') NOT NULL DEFAULT 'active',
  answers JSON NOT NULL,
  revision INT UNSIGNED NOT NULL DEFAULT 0,
  result JSON NULL,
  started_at DATETIME(3) NOT NULL,
  deadline_at DATETIME(3) NOT NULL,
  submitted_at DATETIME(3) NULL,
  INDEX attempt_student(student_id,state,started_at,id),
  CHECK ((entitlement_id IS NULL) <> (monthly_pass_id IS NULL)),
  FOREIGN KEY (monthly_pass_id) REFERENCES de_monthly_passes(id),
  FOREIGN KEY (entitlement_id) REFERENCES de_entitlements(id),
  FOREIGN KEY (student_id) REFERENCES de_students(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_report_jobs (
  id CHAR(36) CHARACTER SET ascii PRIMARY KEY,
  attempt_id CHAR(36) CHARACTER SET ascii NOT NULL UNIQUE,
  state ENUM('ready','leased','sent','failed') NOT NULL DEFAULT 'ready',
  retries INT UNSIGNED NOT NULL DEFAULT 0,
  available_at DATETIME(3) NOT NULL,
  lease_until DATETIME(3) NULL,
  lease_token BINARY(32) NULL,
  report_key VARCHAR(255) CHARACTER SET ascii NULL,
  last_error_code VARCHAR(60) CHARACTER SET ascii NULL,
  INDEX job_ready(state,available_at),
  INDEX job_lease(state,lease_until),
  FOREIGN KEY (attempt_id) REFERENCES de_attempts(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_audit (
  id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
  actor_id CHAR(36) CHARACTER SET ascii NOT NULL,
  action VARCHAR(60) CHARACTER SET ascii NOT NULL,
  target_id VARCHAR(120) CHARACTER SET ascii NOT NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  INDEX audit_actor(actor_id,created_at,id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_admin_roles (
  student_id CHAR(36) CHARACTER SET ascii PRIMARY KEY,
  role ENUM('owner','reviewer') NOT NULL,
  FOREIGN KEY (student_id) REFERENCES de_students(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_integration_settings (
  provider ENUM('google','sms','razorpay','ses') NOT NULL,
  mode ENUM('test','live') NOT NULL,
  encrypted_values BLOB NOT NULL,
  updated_by CHAR(36) CHARACTER SET ascii NOT NULL,
  updated_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  PRIMARY KEY(provider,mode),
  FOREIGN KEY (updated_by) REFERENCES de_students(id)
) ENGINE=InnoDB;

