package in.aitrove.contracts;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.charset.CharacterCodingException;
import java.nio.charset.CodingErrorAction;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.springframework.http.HttpStatus;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.server.ResponseStatusException;

import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class MultipartReceiptImportTest {
    private static final int MAX_BYTES = 128;
    private static final String HEADER = "receipt_id,amount_minor\n";

    @TempDir Path storage;
    private MockMvc client;

    @RestController
    static class UploadController {
        private final Path storage;

        UploadController(Path storage) { this.storage = storage; }

        @PostMapping("/contract/imports")
        String receive(@RequestParam("file") MultipartFile file) throws IOException {
            if (file.isEmpty()) throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Empty upload");
            if (file.getSize() > MAX_BYTES)
                throw new ResponseStatusException(HttpStatus.PAYLOAD_TOO_LARGE, "Upload exceeds fixture limit");

            byte[] content;
            try (var input = file.getInputStream()) {
                content = input.readNBytes(MAX_BYTES + 1);
            }
            if (content.length > MAX_BYTES)
                throw new ResponseStatusException(HttpStatus.PAYLOAD_TOO_LARGE, "Upload exceeds fixture limit");

            String decoded;
            try {
                decoded = StandardCharsets.UTF_8.newDecoder()
                    .onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT)
                    .decode(ByteBuffer.wrap(content)).toString();
            } catch (CharacterCodingException invalid) {
                throw new ResponseStatusException(HttpStatus.UNPROCESSABLE_CONTENT, "Upload must be UTF-8");
            }
            if (!decoded.startsWith(HEADER) || decoded.length() == HEADER.length())
                throw new ResponseStatusException(HttpStatus.UNPROCESSABLE_CONTENT, "Unknown import header");

            // The caller's original filename and MIME declaration never become a storage path.
            Path stored = Files.createTempFile(storage, "receipt-import-", ".csv");
            try {
                Files.write(stored, content);
            } catch (IOException failure) {
                Files.deleteIfExists(stored);
                throw failure;
            }
            return stored.getFileName().toString();
        }
    }

    @BeforeEach void start() {
        client = MockMvcBuilders.standaloneSetup(new UploadController(storage)).build();
    }

    private MockMultipartFile upload(String filename, String mediaType, byte[] content) {
        return new MockMultipartFile("file", filename, mediaType, content);
    }

    private List<Path> storedFiles() throws IOException {
        try (var paths = Files.list(storage)) { return paths.toList(); }
    }

    @Test void storesValidatedBytesUnderGeneratedName() throws Exception {
        byte[] csv = (HEADER + "R-41,2900\n").getBytes(StandardCharsets.UTF_8);
        String generated = client.perform(multipart("/contract/imports")
                .file(upload("../../outside.csv", "text/csv", csv)))
            .andExpect(status().isOk()).andReturn().getResponse().getContentAsString();
        assertTrue(generated.startsWith("receipt-import-"));
        assertFalse(generated.contains(".."));
        assertEquals(List.of(storage.resolve(generated)), storedFiles());
        assertArrayEquals(csv, Files.readAllBytes(storage.resolve(generated)));
    }

    @Test void rejectsOversizedPartBeforeStorage() throws Exception {
        byte[] oversized = (HEADER + "R-41," + "9".repeat(MAX_BYTES) + "\n").getBytes(StandardCharsets.UTF_8);
        client.perform(multipart("/contract/imports").file(upload("large.csv", "text/csv", oversized)))
            .andExpect(status().isPayloadTooLarge());
        assertTrue(storedFiles().isEmpty());
    }

    @Test void rejectsFakeCsvMediaTypeWhenBytesHaveWrongHeader() throws Exception {
        client.perform(multipart("/contract/imports").file(upload("receipts.csv", "text/csv",
                "<html>not a receipt import</html>".getBytes(StandardCharsets.UTF_8))))
            .andExpect(status().isUnprocessableContent());
        assertTrue(storedFiles().isEmpty());
    }

    @Test void rejectsMalformedUtf8BeforeStorage() throws Exception {
        byte[] invalid = (HEADER + "R-41,").getBytes(StandardCharsets.UTF_8);
        byte[] payload = java.util.Arrays.copyOf(invalid, invalid.length + 1);
        payload[payload.length - 1] = (byte) 0xFF;
        client.perform(multipart("/contract/imports").file(upload("receipts.csv", "text/csv", payload)))
            .andExpect(status().isUnprocessableContent());
        assertTrue(storedFiles().isEmpty());
    }

    @Test void rejectsEmptyOrMissingPart() throws Exception {
        client.perform(multipart("/contract/imports").file(upload("empty.csv", "text/csv", new byte[0])))
            .andExpect(status().isBadRequest());
        client.perform(multipart("/contract/imports"))
            .andExpect(status().isBadRequest());
        assertTrue(storedFiles().isEmpty());
    }
}
