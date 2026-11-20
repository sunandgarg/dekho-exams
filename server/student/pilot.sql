-- Applied after schema.sql in the separate student-platform database.
CREATE TABLE IF NOT EXISTS de_school_staff (
  school_id CHAR(36) CHARACTER SET ascii NOT NULL,
  student_id CHAR(36) CHARACTER SET ascii NOT NULL UNIQUE,
  PRIMARY KEY(school_id,student_id),
  FOREIGN KEY(school_id) REFERENCES de_schools(id),
  FOREIGN KEY(student_id) REFERENCES de_students(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_school_coupon_defaults (
  school_id CHAR(36) CHARACTER SET ascii PRIMARY KEY,
  coupon_id CHAR(36) CHARACTER SET ascii NOT NULL UNIQUE,
  encrypted_code BLOB NOT NULL,
  FOREIGN KEY(school_id) REFERENCES de_schools(id),
  FOREIGN KEY(coupon_id) REFERENCES de_coupons(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_school_roster (
  id CHAR(36) CHARACTER SET ascii PRIMARY KEY,
  school_id CHAR(36) CHARACTER SET ascii NOT NULL,
  phone_hash BINARY(32) NOT NULL,
  encrypted_fields BLOB NOT NULL,
  created_at DATETIME(3) NOT NULL DEFAULT CURRENT_TIMESTAMP(3),
  UNIQUE(school_id,phone_hash),
  INDEX(school_id,id),
  FOREIGN KEY(school_id) REFERENCES de_schools(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_platform_invites (
  token_hash BINARY(32) PRIMARY KEY,
  target_kind ENUM('owner','school','student') NOT NULL,
  target_id CHAR(36) CHARACTER SET ascii NOT NULL,
  expires_at DATETIME(3) NOT NULL,
  consumed_at DATETIME(3) NULL,
  INDEX invite_target(target_kind,target_id,consumed_at),
  INDEX invite_expiry(expires_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_platform_roster_accounts (
  roster_id CHAR(36) CHARACTER SET ascii PRIMARY KEY,
  student_id CHAR(36) CHARACTER SET ascii NOT NULL UNIQUE,
  FOREIGN KEY(roster_id) REFERENCES de_school_roster(id),
  FOREIGN KEY(student_id) REFERENCES de_students(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_platform_diagnostics (
  id CHAR(36) CHARACTER SET ascii PRIMARY KEY,
  student_id CHAR(36) CHARACTER SET ascii NOT NULL UNIQUE,
  coupon_id CHAR(36) CHARACTER SET ascii NOT NULL,
  question_set VARCHAR(40) CHARACTER SET ascii NOT NULL,
  answers BLOB NOT NULL,
  revision INT UNSIGNED NOT NULL DEFAULT 0,
  started_at DATETIME(3) NOT NULL,
  deadline_at DATETIME(3) NOT NULL,
  submitted_at DATETIME(3) NULL,
  result BLOB NULL,
  FOREIGN KEY(student_id) REFERENCES de_students(id),
  FOREIGN KEY(coupon_id) REFERENCES de_coupons(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_platform_otp (
  roster_id CHAR(36) CHARACTER SET ascii PRIMARY KEY,
  invite_hash BINARY(32) NOT NULL,
  code_hash BINARY(32) NOT NULL,
  expires_at DATETIME(3) NOT NULL,
  next_send_at DATETIME(3) NOT NULL,
  attempts TINYINT UNSIGNED NOT NULL DEFAULT 0,
  FOREIGN KEY(roster_id) REFERENCES de_school_roster(id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS de_platform_sms_budget (
  utc_day DATE PRIMARY KEY,
  sends INT UNSIGNED NOT NULL DEFAULT 0
) ENGINE=InnoDB;
