import java.sql.*;
public class ReceiptDatabaseProject {
    static void store(Connection connection,String id,int quantity) throws SQLException {
        if(id==null||id.isEmpty()||quantity<=0)throw new IllegalArgumentException("Invalid receipt");
        if(connection.getAutoCommit())throw new IllegalArgumentException("Manual transaction required");
        try{
            try(PreparedStatement detail=connection.prepareStatement("INSERT INTO receipts(id,quantity) VALUES(?,?)")){
                detail.setString(1,id);detail.setInt(2,quantity);detail.executeUpdate();
            }
            try(PreparedStatement total=connection.prepareStatement("UPDATE totals SET quantity=quantity+? WHERE id=1")){
                total.setInt(1,quantity);if(total.executeUpdate()!=1)throw new SQLException("Aggregate row missing");
            }
            connection.commit();
        }catch(SQLException failure){
            try{connection.rollback();}catch(SQLException rollback){failure.addSuppressed(rollback);}
            throw failure;
        }
    }
    public static void main(String[] args) throws Exception {
        try(Connection connection=DriverManager.getConnection("jdbc:h2:mem:receipt_project")){
            try(Statement schema=connection.createStatement()){
                schema.execute("CREATE TABLE receipts(id VARCHAR(80) PRIMARY KEY,quantity INT CHECK(quantity>0))");
                schema.execute("CREATE TABLE totals(id INT PRIMARY KEY,quantity INT)");
                schema.execute("INSERT INTO totals VALUES(1,0)");
            }
            connection.setAutoCommit(false);store(connection,"R-81",7);
            try{store(connection,"R-81",5);}catch(SQLIntegrityConstraintViolationException duplicate){System.out.println("Duplicate rejected");}
            try(Statement query=connection.createStatement();ResultSet total=query.executeQuery("SELECT quantity FROM totals WHERE id=1")){
                total.next();System.out.println("total="+total.getInt(1));
            }
            try(Statement query=connection.createStatement();ResultSet rows=query.executeQuery("SELECT COUNT(*) FROM receipts")){
                rows.next();System.out.println("rows="+rows.getInt(1));
            }
        }
    }
}
