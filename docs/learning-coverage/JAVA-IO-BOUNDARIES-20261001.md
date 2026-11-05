# Java I/O boundary batch — editorial handoff

Ten Java tutorials were added under the Advanced Java module, "I/O framing and memory boundaries." Each has a runnable Java program, checked output, explicit cost and ownership notes, Common Mistakes, and links to related AITrove lessons. Existing byte-stream, file-channel, UTF-8, ZIP, file, and ByteBuffer lessons link back into the batch.

New paths: `inputstream-short-read-loop`, `readnbytes-truncated-frame`, `datainputstream-readfully-eof`, `charsetdecoder-report-policy`, `bytebuffer-flip-compact-state`, `writable-channel-short-write`, `zip-entry-expanded-limit`, `bounded-line-reader`, `inputstream-available-not-length`, and `bytebuffer-slice-ownership` under `/java/`.

Research was used to verify API contracts and identify gaps. The public tutorial bodies have fresh examples and explanations and contain no external source URLs. This does not make Java APIs, behavior, or terminology exclusive AITrove property; a numeric AI-detector result is neither measured nor guaranteed.

User-prioritized inventory references, in order:

1. https://docs.oracle.com/javase/8/docs/api/java/util/LinkedList.html
2. https://www.geeksforgeeks.org/java/java/
3. https://www.w3schools.com/java/java_linkedlist.asp
4. https://beginnersbook.com/2013/12/linkedlist-in-java-with-example/
5. https://codingnomads.com/java-301-linked-lists

Primary API checks for this batch:

- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/io/InputStream.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/io/DataInputStream.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/charset/CharsetDecoder.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/ByteBuffer.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/nio/channels/FileChannel.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/zip/ZipInputStream.html

Remaining Java work is open ended. In particular: production socket deadlines and cancellation, adversarial streaming tests for high compression ratios and many-entry archives, crash-safe file publication under real filesystem faults, target-database behavior, a broader Java release matrix, more DSA proof and stress cases, and a larger judged exercise/quiz bank. The code fixtures here check stated local contracts; they do not establish network, deployment, or durability behavior.
