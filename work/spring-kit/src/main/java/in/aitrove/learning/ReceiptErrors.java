package in.aitrove.learning;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
@RestControllerAdvice
public class ReceiptErrors {
    @ExceptionHandler(ReceiptController.MissingReceipt.class)
    ProblemDetail missing(ReceiptController.MissingReceipt failure) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, failure.getMessage());
    }
    @ExceptionHandler({IllegalArgumentException.class, MethodArgumentNotValidException.class})
    ProblemDetail rejected(Exception failure) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, "Receipt input is invalid");
    }
}
