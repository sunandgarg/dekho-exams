import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

public class ReceiptLookup {
    static String status(Connection connection, String receiptId) throws SQLException {
        try (PreparedStatement query = connection.prepareStatement(
                "SELECT status FROM receipts WHERE receipt_id = ?")) {
            query.setString(1, receiptId);
            try (ResultSet rows = query.executeQuery()) {
                return rows.next() ? rows.getString(1) : null;
            }
        }
    }
    public static void main(String[] args) throws SQLException {
        try (Connection connection = DriverManager.getConnection("jdbc:h2:mem:receipts")) {
            try (PreparedStatement schema = connection.prepareStatement(
                    "CREATE TABLE receipts(receipt_id VARCHAR PRIMARY KEY, status VARCHAR)")) {
                schema.executeUpdate();
            }
            try (PreparedStatement insert = connection.prepareStatement(
                    "INSERT INTO receipts VALUES (?, ?)")) {
                insert.setString(1, "rcpt-'54");
                insert.setString(2, "paid");
                insert.executeUpdate();
            }
            System.out.println(status(connection, "rcpt-'54"));
            System.out.println(status(connection, "absent"));
        }
    }
}
