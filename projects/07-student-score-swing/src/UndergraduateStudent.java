import java.io.Serializable;

/**
 * 本科生类，继承自 Student 类
 */
public class UndergraduateStudent extends Student implements Serializable {
    private static final long serialVersionUID = 1L; // 添加序列化版本号

    public UndergraduateStudent(String studentId, String name, String className,
                                double chinese, double math, double english) {
        super(studentId, name, className, chinese, math, english);
    }

    @Override
    public String getType() {
        return "本科生";
    }
}