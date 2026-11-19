import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.File;

/**
 * 截图辅助：把主窗口（含学生列表）渲染成 PNG。
 * 不依赖屏幕坐标与 DPI 缩放，直接绘制组件树。
 */
public class Shot {
    public static void main(String[] args) throws Exception {
        final String outDir = args.length > 0 ? args[0] : "docs";
        new File(outDir).mkdirs();

        javax.swing.SwingUtilities.invokeAndWait(() -> {
            try {
                // 登录页
                LoginGUI login = new LoginGUI();
                login.setVisible(true);
                Thread.sleep(1200);
                save(login, new File(outDir, "screenshot-login.png"));
                login.dispose();

                // 主界面：先切到"查看所有学生"
                MainGUI main = new MainGUI();
                main.setVisible(true);
                Thread.sleep(800);
                try {
                    java.lang.reflect.Method m = MainGUI.class.getDeclaredMethod("viewAllStudents");
                    m.setAccessible(true);
                    m.invoke(main);
                } catch (Exception ignore) {
                }
                Thread.sleep(800);
                save(main, new File(outDir, "screenshot.png"));
                main.dispose();
            } catch (Exception e) {
                e.printStackTrace();
            }
        });

        System.out.println("saved to " + new File(outDir).getAbsolutePath());
        System.exit(0);
    }

    private static void save(java.awt.Window w, File f) throws Exception {
        int width = Math.max(w.getWidth(), 100);
        int height = Math.max(w.getHeight(), 100);
        BufferedImage img = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);
        java.awt.Graphics2D g = img.createGraphics();
        g.setColor(java.awt.Color.WHITE);
        g.fillRect(0, 0, width, height);
        w.paint(g);
        g.dispose();
        ImageIO.write(img, "png", f);
        System.out.println("wrote " + f.getAbsolutePath() + " " + f.length() + " bytes");
    }
}
