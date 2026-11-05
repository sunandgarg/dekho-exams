# Java numeric representation boundaries — editorial handoff

Ten original Java tutorials were added to the Java Tutorial module, "Numeric representation boundaries." Each has a complete program, verified output, cost and failure notes, Common Mistakes, and internal links. Six existing arithmetic, decimal, and collection lessons link back into the new module.

New `/java/` paths: `math-abs-min-value`, `floor-div-mod-negative`, `bigdecimal-divide-rounding`, `bigdecimal-setscale-unnecessary`, `biginteger-exact-conversion`, `double-nan-collection-contracts`, `double-finite-validation`, `floating-sum-order`, `unsigned-integer-parsing`, and `long-to-double-precision`.

The user-prioritized LinkedList and general Java pages were checked for curriculum inventory, not copied. Primary API checks for this numeric batch:

- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Math.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/math/BigDecimal.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/math/BigInteger.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Double.html
- https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/Integer.html

The public lesson bodies contain no external URLs. `Math.absExact` is labeled Java 15+; the other programs target Java 8. These local fixtures are not a full numeric audit of every arithmetic path. Further work includes precision budgets in real pipelines, target-database decimal column behavior, unsigned wire formats, and property-based tests for boundary inputs. Java API facts are not exclusive property, and no AI-detector score was measured.
