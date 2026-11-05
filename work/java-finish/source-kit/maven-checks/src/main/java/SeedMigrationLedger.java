import java.sql.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
public class SeedMigrationLedger {
    static String checksum(String definition)throws Exception{
        byte[] digest=MessageDigest.getInstance("SHA-256").digest(definition.getBytes(StandardCharsets.UTF_8));StringBuilder value=new StringBuilder();for(byte part:digest)value.append(String.format("%02x",part&255));return value.toString();
    }
    static boolean apply(Connection connection,String definition)throws Exception{
        String digest=checksum(definition);connection.setAutoCommit(false);
        try{
            try(PreparedStatement query=connection.prepareStatement("SELECT checksum FROM versions WHERE version=1");ResultSet rows=query.executeQuery()){
                if(rows.next()){if(!digest.equals(rows.getString(1)))throw new IllegalStateException("Migration definition changed");connection.commit();return false;}
            }
            try(PreparedStatement seed=connection.prepareStatement("INSERT INTO labels VALUES(?,?)")){seed.setInt(1,31);seed.setString(2,"Ready");seed.executeUpdate();}
            try(PreparedStatement record=connection.prepareStatement("INSERT INTO versions VALUES(1,?)")){record.setString(1,digest);record.executeUpdate();}connection.commit();return true;
        }catch(Exception failure){try{connection.rollback();}catch(SQLException rollback){failure.addSuppressed(rollback);}throw failure;}
    }
    public static void main(String[] args)throws Exception{
        try(Connection database=DriverManager.getConnection("jdbc:h2:mem:migration_"+java.util.UUID.randomUUID())){
            try(Statement schema=database.createStatement()){schema.execute("CREATE TABLE versions(version INT PRIMARY KEY, checksum VARCHAR(64))");schema.execute("CREATE TABLE labels(id INT PRIMARY KEY, label VARCHAR(40))");}
            System.out.println(apply(database,"seed-label-31-v1"));System.out.println(apply(database,"seed-label-31-v1"));
            try{apply(database,"seed-label-31-edited");}catch(IllegalStateException changed){System.out.println(changed.getMessage());}
        }
    }
}
