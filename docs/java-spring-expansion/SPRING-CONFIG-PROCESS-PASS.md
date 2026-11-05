# Spring configuration process pass

The Spring & Spring Boot subject is separate from Java. This pass adds six original lessons, one 12-question quiz, and a five-case child-JVM fixture. The subject now has 175 articles, 10 section hubs, eight quizzes with 145 questions, and 1,496 links inside Spring article bodies. All new lessons appear in their section modules; the Spring content check found no orphaned pages.

## What was checked

`RelaySettingsProcessTest` starts a distinct non-web Spring Boot JVM. It checks canonical `RELAY_BATCHSIZE` and `RELAY_TIMEOUT` binding, a command-line value winning over the environment, validation of an invalid environment value, a relative import loaded while the child starts in another directory, and startup failure for a missing required relative import. The full Maven suite passes 137 tests with no failures or skips. The source download includes these tests and their small probe entry point.

The new lessons are `/spring/boot-env-process-binding`, `/spring/boot-env-cli-precedence`, `/spring/boot-env-validation-failure`, `/spring/boot-relative-import-process`, `/spring/boot-missing-import-process`, and `/spring/boot-config-process-test-boundary`. The quiz is `/quizzes/spring-config-process`. Existing environment, import, source-matrix and testing pages now link back to them. This extends the existing Spring material rather than placing it under Java.

## Evidence limits

The probe is not the runnable `ReceiptApplication`. It does not read a real deployment mount or secret store, run in a container, use a target production database, or test rollout traffic. The import test has one relative child file; it does not test a second-level import declared by that child file. The site must not describe these boundaries as complete production verification.

The Spring content uses original examples and prose tied to the local fixture. Reference sites informed topic selection and fact checking; no reference prose or examples were copied into these pages.
