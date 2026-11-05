package in.aitrove.contracts;

import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

import graphql.ExecutionInput;
import graphql.ExecutionResult;
import graphql.schema.DataFetchingEnvironment;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.graphql.execution.GraphQlSource;

import static org.junit.jupiter.api.Assertions.*;

class GraphQlBoundaryContractTest {
    private static final String SCHEMA = """
            type Query {
              receipt(id: ID!): Receipt
              receipts(limit: Int!): [Receipt!]!
            }
            type Mutation {
              reserve(id: ID!, units: Int!, expectedVersion: Int!): Receipt
            }
            type Receipt {
              id: ID!
              tenant: String!
              available: Int!
              version: Int!
            }
            """;

    record Receipt(String id, String tenant, int available, int version) {}

    private final Map<String, Receipt> ledger = new ConcurrentHashMap<>();
    private GraphQlSource source;

    @BeforeEach
    void prepareSchema() {
        ledger.clear();
        ledger.put("RC-47", new Receipt("RC-47", "north", 19, 3));
        ledger.put("RC-52", new Receipt("RC-52", "north", 11, 1));
        ledger.put("RC-63", new Receipt("RC-63", "south", 27, 2));
        source = GraphQlSource.schemaResourceBuilder()
                .schemaResources(new ByteArrayResource(SCHEMA.getBytes(StandardCharsets.UTF_8)))
                .configureRuntimeWiring(wiring -> {
                    wiring.type("Query", type -> type
                            .dataFetcher("receipt", this::receipt)
                            .dataFetcher("receipts", this::receipts));
                    wiring.type("Mutation", type -> type.dataFetcher("reserve", this::reserve));
                })
                .build();
    }

    private Receipt receipt(DataFetchingEnvironment environment) {
        Receipt found = ledger.get(environment.getArgument("id"));
        return found != null && found.tenant().equals(tenant(environment)) ? found : null;
    }

    private List<Receipt> receipts(DataFetchingEnvironment environment) {
        int limit = environment.getArgument("limit");
        if (limit < 1 || limit > 25) throw new IllegalArgumentException("limit outside 1..25");
        return ledger.values().stream()
                .filter(receipt -> receipt.tenant().equals(tenant(environment)))
                .sorted((left, right) -> left.id().compareTo(right.id()))
                .limit(limit)
                .toList();
    }

    private Receipt reserve(DataFetchingEnvironment environment) {
        String id = environment.getArgument("id");
        int units = environment.getArgument("units");
        int expectedVersion = environment.getArgument("expectedVersion");
        if (units <= 0) throw new IllegalArgumentException("units must be positive");
        Receipt result = ledger.computeIfPresent(id, (ignored, current) -> {
            if (!current.tenant().equals(tenant(environment))) return current;
            if (current.version() != expectedVersion) throw new IllegalStateException("stale receipt version");
            if (current.available() < units) throw new IllegalStateException("insufficient stock");
            return new Receipt(current.id(), current.tenant(), current.available() - units, current.version() + 1);
        });
        return result != null && result.tenant().equals(tenant(environment)) ? result : null;
    }

    private String tenant(DataFetchingEnvironment environment) {
        return environment.getGraphQlContext().get("tenant");
    }

    private ExecutionResult execute(String tenant, String document) {
        return source.graphQl().execute(ExecutionInput.newExecutionInput()
                .query(document).graphQLContext(Map.of("tenant", tenant)).build());
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> data(ExecutionResult result) {
        return result.getData();
    }

    @Test
    void selectedFieldsAreReturnedForAuthorizedTenant() {
        ExecutionResult result = execute("north", "{ receipt(id: \"RC-47\") { id available } }");
        assertTrue(result.getErrors().isEmpty());
        Map<String, Object> receipt = (Map<String, Object>) data(result).get("receipt");
        assertEquals("RC-47", receipt.get("id"));
        assertEquals(19, receipt.get("available"));
        assertFalse(receipt.containsKey("tenant"));
    }

    @Test
    void tenantCannotReadAnotherTenantsReceipt() {
        ExecutionResult result = execute("south", "{ receipt(id: \"RC-47\") { id } }");
        assertTrue(result.getErrors().isEmpty());
        assertNull(data(result).get("receipt"));
    }

    @Test
    void listIsTenantScopedAndBounded() {
        ExecutionResult result = execute("north", "{ receipts(limit: 1) { id } }");
        assertTrue(result.getErrors().isEmpty());
        List<Map<String, Object>> receipts = (List<Map<String, Object>>) data(result).get("receipts");
        assertEquals(1, receipts.size());
        assertEquals("RC-47", receipts.getFirst().get("id"));
    }

    @Test
    void oversizedListRequestReturnsGraphQlError() {
        ExecutionResult result = execute("north", "{ receipts(limit: 47) { id } }");
        assertFalse(result.getErrors().isEmpty());
        assertNull(result.getData());
    }

    @Test
    void mutationUsesVersionAndDecrementsOnce() {
        ExecutionResult result = execute("north", "mutation { reserve(id: \"RC-47\", units: 7, expectedVersion: 3) { available version } }");
        assertTrue(result.getErrors().isEmpty());
        Map<String, Object> receipt = (Map<String, Object>) data(result).get("reserve");
        assertEquals(12, receipt.get("available"));
        assertEquals(4, receipt.get("version"));
        assertEquals(12, ledger.get("RC-47").available());
    }

    @Test
    void staleMutationReturnsErrorWithoutAnotherDebit() {
        execute("north", "mutation { reserve(id: \"RC-47\", units: 7, expectedVersion: 3) { id } }");
        ExecutionResult stale = execute("north", "mutation { reserve(id: \"RC-47\", units: 2, expectedVersion: 3) { id } }");
        assertFalse(stale.getErrors().isEmpty());
        assertEquals(12, ledger.get("RC-47").available());
    }

    @Test
    void wrongTenantMutationDoesNotChangeTarget() {
        ExecutionResult result = execute("south", "mutation { reserve(id: \"RC-47\", units: 7, expectedVersion: 3) { id } }");
        assertTrue(result.getErrors().isEmpty());
        assertNull(data(result).get("reserve"));
        assertEquals(19, ledger.get("RC-47").available());
    }

    @Test
    void missingRequiredArgumentIsRejectedBeforeFetcher() {
        ExecutionResult result = execute("north", "{ receipts { id } }");
        assertFalse(result.getErrors().isEmpty());
        assertEquals(19, ledger.get("RC-47").available());
    }
}
