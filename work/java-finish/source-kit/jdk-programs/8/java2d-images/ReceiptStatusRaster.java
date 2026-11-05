import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import javax.imageio.ImageIO;
public class ReceiptStatusRaster {
    public static void main(String[] args) throws Exception {
        BufferedImage image = new BufferedImage(40, 20, BufferedImage.TYPE_INT_ARGB);
        Graphics2D paint = image.createGraphics();
        try { paint.setColor(new Color(20, 70, 100)); paint.fillRect(4, 3, 8, 6); }
        finally { paint.dispose(); }
        ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        if (!ImageIO.write(image, "png", bytes)) throw new IllegalStateException("Missing PNG encoder");
        BufferedImage restored = ImageIO.read(new ByteArrayInputStream(bytes.toByteArray()));
        if (restored == null) throw new IllegalStateException("PNG decode failed");
        System.out.println(restored.getWidth()+"x"+restored.getHeight());
        System.out.println(restored.getRGB(4, 3) == new Color(20, 70, 100).getRGB());
        System.out.println(restored.getRGB(0, 0) == 0);
    }
}
