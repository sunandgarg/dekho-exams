import com.zaxxer.hikari.*;
import java.sql.*;
public class PooledReceiptBoundary {
    public static void main(String[] args)throws Exception{
        HikariConfig config=new HikariConfig();config.setJdbcUrl("jdbc:h2:mem:pool_"+java.util.UUID.randomUUID()+";DB_CLOSE_DELAY=-1");config.setMaximumPoolSize(1);config.setMinimumIdle(0);config.setConnectionTimeout(300);config.setAutoCommit(false);
        try(HikariDataSource pool=new HikariDataSource(config)){
            try(Connection connection=pool.getConnection()){
                try(Statement sql=connection.createStatement()){sql.execute("CREATE TABLE receipts(id INT PRIMARY KEY)");}
                try(PreparedStatement insert=connection.prepareStatement("INSERT INTO receipts VALUES(?)")){insert.setInt(1,17);insert.executeUpdate();}connection.rollback();
            }
            try(Connection held=pool.getConnection()){
                try(Statement query=held.createStatement();ResultSet rows=query.executeQuery("SELECT COUNT(*) FROM receipts")){rows.next();System.out.println(rows.getInt(1));}
                try(Connection unexpected=pool.getConnection()){throw new IllegalStateException("Second borrow admitted");}
                catch(SQLTransientConnectionException saturated){System.out.println("pool timeout");}held.rollback();
            }
            try(Connection again=pool.getConnection()){System.out.println(again.isValid(1));again.rollback();}
        }
    }
}
