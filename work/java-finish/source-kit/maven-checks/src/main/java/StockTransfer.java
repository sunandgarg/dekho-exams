import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

public class StockTransfer {
    static void transfer(Connection connection, String source, String target, int units)
            throws SQLException {
        if (units <= 0) throw new IllegalArgumentException("Units must be positive");
        if (connection.getAutoCommit()) throw new IllegalStateException("Transaction required");
        try (PreparedStatement debit = connection.prepareStatement(
                    "UPDATE stock SET units = units - ? WHERE site = ? AND units >= ?");
             PreparedStatement credit = connection.prepareStatement(
                    "UPDATE stock SET units = units + ? WHERE site = ?")) {
            debit.setInt(1, units); debit.setString(2, source); debit.setInt(3, units);
            if (debit.executeUpdate() != 1) throw new SQLException("Insufficient stock");
            credit.setInt(1, units); credit.setString(2, target);
            if (credit.executeUpdate() != 1) throw new SQLException("Unknown target");
            connection.commit();
        } catch (SQLException failure) {
            try { connection.rollback(); }
            catch (SQLException rollbackFailure) { failure.addSuppressed(rollbackFailure); }
            throw failure;
        }
    }
    public static void main(String[] args) throws SQLException {
        try (Connection connection = DriverManager.getConnection("jdbc:h2:mem:stock")) {
            try (PreparedStatement schema = connection.prepareStatement(
                    "CREATE TABLE stock(site VARCHAR PRIMARY KEY, units INT CHECK(units >= 0))")) {
                schema.executeUpdate();
            }
            try (PreparedStatement seed = connection.prepareStatement(
                    "INSERT INTO stock VALUES ('north', 10), ('south', 2)")) {
                seed.executeUpdate();
            }
            connection.setAutoCommit(false);
            transfer(connection, "north", "south", 3);
            try { transfer(connection, "north", "missing", 2); }
            catch (SQLException expected) { System.out.println("failed transfer rolled back"); }
            try (PreparedStatement query = connection.prepareStatement("SELECT site, units FROM stock ORDER BY site");
                 ResultSet rows = query.executeQuery()) {
                while (rows.next()) System.out.println(rows.getString(1) + "=" + rows.getInt(2));
            }
            connection.rollback();
        }
    }
}
