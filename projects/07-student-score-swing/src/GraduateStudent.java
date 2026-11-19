import java.io.Serializable;

/**
 * 研究生类，继承自 Student 类
 */
public class GraduateStudent extends Student implements Serializable {
    private static final long serialVersionUID = 1L; // 添加序列化版本号

    public GraduateStudent(String studentId, String name, String className,
                           double chinese, double math, double english) {
        super(studentId, name, className, chinese, math, english);
    }

    @Override
    public String getType() {
        return "研究生";
    }
}
