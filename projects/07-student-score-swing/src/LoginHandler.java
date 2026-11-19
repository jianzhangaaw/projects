public class LoginHandler {
    private static final String VALID_USERNAME = "8002124117";
    private static final String VALID_PASSWORD = "123456";

    public static boolean authenticate(String username, String password) {
        return VALID_USERNAME.equals(username) && VALID_PASSWORD.equals(password);
    }
}