package in.aitrove.contracts;
import org.springframework.security.access.prepost.PreAuthorize;
public class AuthorizedReceiptRead {
    @PreAuthorize("hasAuthority('receipt:read')")
    public String receipt(long id) { return "receipt:"+id; }
}
