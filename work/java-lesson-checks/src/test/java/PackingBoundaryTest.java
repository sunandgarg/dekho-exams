import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import static org.junit.jupiter.api.Assertions.*;
public class PackingBoundaryTest {
    static int vehicles(int parcels,int capacity){
        if(parcels<0||capacity<=0)throw new IllegalArgumentException("Invalid packing inputs");
        return parcels/capacity+(parcels%capacity==0?0:1);
    }
    @ParameterizedTest
    @CsvSource({"0,4,0","1,4,1","8,4,2","9,4,3","2147483647,2,1073741824"})
    void validInputs(int parcels,int capacity,int expected){assertEquals(expected,vehicles(parcels,capacity));}
    @ParameterizedTest
    @CsvSource({"-1,4","1,0","1,-4"})
    void rejectsInvalidInputs(int parcels,int capacity){assertThrows(IllegalArgumentException.class,()->vehicles(parcels,capacity));}
}
