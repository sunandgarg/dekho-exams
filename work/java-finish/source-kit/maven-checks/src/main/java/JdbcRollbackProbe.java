import java.sql.*;
public class JdbcRollbackProbe {
    public static void main(String[] args) throws Exception {
        try(Connection connection=DriverManager.getConnection("jdbc:h2:mem:rollback_probe")){
            try(Statement schema=connection.createStatement()){schema.execute("CREATE TABLE receipts(id INT PRIMARY KEY)");}
            connection.setAutoCommit(false);
            try(PreparedStatement insert=connection.prepareStatement("INSERT INTO receipts(id) VALUES(?)")){
                insert.setInt(1,42);insert.executeUpdate();
            }
            connection.rollback();
            try(Statement query=connection.createStatement();ResultSet result=query.executeQuery("SELECT COUNT(*) FROM receipts")){
                result.next();System.out.println("rows="+result.getInt(1));
            }
        }
    }
}
