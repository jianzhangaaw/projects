import javax.swing.*;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

/**
 * 登录界面
 */
public class LoginGUI extends JFrame {
    private JTextField usernameField;
    private JPasswordField passwordField;
    private static final String VALID_USERNAME = "8002124117";
    private static final String VALID_PASSWORD = "123456";

    public LoginGUI() {
        setTitle("系统登录");
        setSize(350, 200);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);
        setResizable(false);

        // 创建主面板
        JPanel mainPanel = new JPanel(new BorderLayout());
        mainPanel.setBorder(BorderFactory.createEmptyBorder(20, 20, 20, 20));

        // 创建标题面板
        JPanel titlePanel = new JPanel();
        JLabel titleLabel = new JLabel("学生成绩管理系统");
        titleLabel.setFont(new Font("宋体", Font.BOLD, 16));
        titlePanel.add(titleLabel);
        mainPanel.add(titlePanel, BorderLayout.NORTH);

        // 创建输入面板
        JPanel inputPanel = new JPanel(new GridLayout(3, 2, 10, 10));
        usernameField = new JTextField();
        passwordField = new JPasswordField();

        inputPanel.add(new JLabel("账号:"));
        inputPanel.add(usernameField);
        inputPanel.add(new JLabel("密码:"));
        inputPanel.add(passwordField);
        inputPanel.add(new JLabel()); // 占位

        mainPanel.add(inputPanel, BorderLayout.CENTER);

        // 创建按钮面板
        JPanel buttonPanel = new JPanel();
        JButton loginButton = new JButton("登录");
        JButton exitButton = new JButton("退出");

        loginButton.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                String username = usernameField.getText().trim();
                String password = new String(passwordField.getPassword());

                if (VALID_USERNAME.equals(username) && VALID_PASSWORD.equals(password)) {
                    JOptionPane.showMessageDialog(LoginGUI.this, "登录成功！", "提示", JOptionPane.INFORMATION_MESSAGE);
                    dispose(); // 关闭登录窗口
                    // 打开主界面
                    SwingUtilities.invokeLater(() -> {
                        MainGUI mainGUI = new MainGUI();
                        mainGUI.setVisible(true);
                    });
                } else {
                    JOptionPane.showMessageDialog(LoginGUI.this, "账号或密码错误！", "错误", JOptionPane.ERROR_MESSAGE);
                    passwordField.setText("");
                }
            }
        });

        exitButton.addActionListener(new ActionListener() {
            @Override
            public void actionPerformed(ActionEvent e) {
                System.exit(0);
            }
        });

        buttonPanel.add(loginButton);
        buttonPanel.add(exitButton);
        mainPanel.add(buttonPanel, BorderLayout.SOUTH);

        add(mainPanel);
    }

    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            LoginGUI loginGUI = new LoginGUI();
            loginGUI.setVisible(true);
        });
    }
}    