import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import javax.swing.JLabel;
import javax.swing.SwingUtilities;
import javax.swing.SwingWorker;
public class ReceiptViewerWorker {
    public static void main(String[] args) throws Exception {
        AtomicReference<String> observed = new AtomicReference<>();
        CountDownLatch completed = new CountDownLatch(1);
        SwingUtilities.invokeAndWait(() -> {
            JLabel label = new JLabel("Waiting");
            SwingWorker<Integer, Void> worker = new SwingWorker<Integer, Void>() {
                protected Integer doInBackground() {
                    if (SwingUtilities.isEventDispatchThread()) throw new IllegalStateException("Work on UI thread");
                    return 6;
                }
                protected void done() {
                    try {
                        if (!SwingUtilities.isEventDispatchThread()) throw new IllegalStateException("Completion off UI thread");
                        label.setText("Imported="+get()); observed.set(label.getText());
                    } catch (InterruptedException failure) { Thread.currentThread().interrupt(); observed.set("interrupted"); }
                    catch (Exception failure) { observed.set("failed"); }
                    finally { completed.countDown(); }
                }
            };
            worker.execute();
        });
        if (!completed.await(5, TimeUnit.SECONDS)) throw new IllegalStateException("Completion deadline");
        System.out.println(observed.get());
    }
}
