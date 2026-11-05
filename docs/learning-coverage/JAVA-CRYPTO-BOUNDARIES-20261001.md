# Java cryptographic API boundaries — editorial handoff

Eight original Java 8 tutorials were added to the Java Tutorial module, "Cryptographic API boundaries." They cover explicit UTF-8 digest inputs, ByteBuffer consumption, HMAC verification, length-framed MAC input, SecureRandom token encoding, AES-GCM tamper rejection, AES-GCM associated data, and Base64 alphabets. Five existing Java lessons link back into the module. Every new lesson contains a runnable program, checked output, cost and failure notes, Common Mistakes, and internal links.

New `/java/` paths: `sha256-explicit-utf8`, `message-digest-bytebuffer`, `hmac-sha256-verify`, `hmac-field-framing`, `secure-random-token-encoding`, `aes-gcm-authenticated-decryption`, `aes-gcm-associated-data`, and `base64-url-vs-basic`.

The five user-prioritized Java and LinkedList pages were checked for curriculum context, not copied. API and security-boundary checks used:

- https://docs.oracle.com/javase/8/docs/api/java/security/MessageDigest.html
- https://docs.oracle.com/javase/8/docs/api/javax/crypto/Mac.html
- https://docs.oracle.com/javase/8/docs/api/javax/crypto/Cipher.html
- https://docs.oracle.com/javase/8/docs/api/javax/crypto/spec/GCMParameterSpec.html
- https://docs.oracle.com/javase/8/docs/api/java/security/SecureRandom.html
- https://docs.oracle.com/javase/8/docs/api/java/util/Base64.html
- https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
- https://cheatsheetseries.owasp.org/cheatsheets/Java_Security_Cheat_Sheet.html

The public lesson bodies contain no external URLs or copied example code. Each program is compiled for Java 8 and executed five times each on local JDK 21 and JDK 25; output, semantic tags, internal targets, and the Java module are checked. Randomized examples report only stable properties, never a generated key or token.

These examples are API boundary lessons, not a complete production cryptosystem. Production work still needs protected key storage and rotation, durable nonce-uniqueness design, versioned serialization, abuse limits, and specialist review. No AI-detector score was measured; Java API facts and standard cryptographic primitives are not exclusive property.
