import java.sql.*;
public class ReceiptIsolationSessions {
    static int read(Connection connection)throws SQLException{
        try(PreparedStatement query=connection.prepareStatement("SELECT units FROM stock WHERE id=1");ResultSet rows=query.executeQuery()){if(!rows.next())throw new SQLException("Missing stock");return rows.getInt(1);}
    }
    public static void main(String[] args)throws Exception{
        String url="jdbc:h2:mem:isolation_"+java.util.UUID.randomUUID();
        try(Connection writer=DriverManager.getConnection(url);Connection reader=DriverManager.getConnection(url)){
            try(Statement schema=writer.createStatement()){schema.execute("CREATE TABLE stock(id INT PRIMARY KEY, units INT)");schema.executeUpdate("INSERT INTO stock VALUES(1,7)");}
            reader.setTransactionIsolation(Connection.TRANSACTION_READ_COMMITTED);writer.setAutoCommit(false);
            try{
                try(PreparedStatement update=writer.prepareStatement("UPDATE stock SET units=? WHERE id=1")){update.setInt(1,11);if(update.executeUpdate()!=1)throw new SQLException("Missing update");}
                System.out.println(read(reader));writer.commit();System.out.println(read(reader));
            }finally{writer.rollback();}
        }
    }
}
