import java.io.*;
import java.util.ArrayList;
import java.util.List;

/**
 * 文件处理类，负责学生数据的读写操作
 */
public class FileHandler {
    private static final String FILE_PATH = "students.dat"; // 数据文件路径

    // 获取数据文件
    private File getDataFile() {
        return new File(System.getProperty("user.dir"), FILE_PATH);
    }

    // 保存学生数据到文件
    public boolean saveStudents(List<Student> students) {
        File file = getDataFile();

        try (ObjectOutputStream oos = new ObjectOutputStream(new FileOutputStream(file))) {
            oos.writeObject(students);
            System.out.println("数据已成功保存到: " + file.getAbsolutePath());
            return true;
        } catch (IOException e) {
            System.err.println("保存文件失败: " + e.getMessage());
            e.printStackTrace();
            return false;
        }
    }

    // 从文件加载学生数据
    @SuppressWarnings("unchecked")
    public List<Student> loadStudents() {
        List<Student> students = new ArrayList<>();
        File file = getDataFile();

        if (!file.exists()) {
            System.out.println("数据文件不存在，将创建新文件: " + file.getAbsolutePath());
            return students;
        }

        try (ObjectInputStream ois = new ObjectInputStream(new FileInputStream(file))) {
            students = (List<Student>) ois.readObject();
            System.out.println("成功从文件加载 " + students.size() + " 条学生数据");
        } catch (FileNotFoundException e) {
            System.out.println("数据文件未找到: " + file.getAbsolutePath());
        } catch (IOException | ClassNotFoundException e) {
            System.err.println("加载文件失败: " + e.getMessage());
            e.printStackTrace();
        }

        return students;
    }

    // 检查文件是否存在
    public boolean fileExists() {
        return getDataFile().exists();
    }

    // 获取文件路径
    public String getFilePath() {
        return getDataFile().getAbsolutePath();
    }
}