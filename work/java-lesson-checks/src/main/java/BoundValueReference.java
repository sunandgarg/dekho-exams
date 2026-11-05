import java.sql.*;
public class BoundValueReference {
    public static void main(String[] args) throws Exception {
        try(Connection connection=DriverManager.getConnection("jdbc:h2:mem:parameter_reference");
            PreparedStatement query=connection.prepareStatement("SELECT ?")){
            query.setString(1,"customer'42");
            try(ResultSet result=query.executeQuery()){
                result.next();System.out.println(result.getString(1));
            }
        }
    }
}
