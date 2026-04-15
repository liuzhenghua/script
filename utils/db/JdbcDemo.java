/**
 JDBC 操作数据库示例示例
 注意：老版本JDBC驱动返回的是Timestamp类型，新驱动返回LocalDateTime，建议升级驱动

 <dependencies>
    <!-- JDBC 驱动 -->
    <dependency>
        <groupId>com.mysql</groupId>
        <artifactId>mysql-connector-j</artifactId>
        <version>8.3.0</version>
    </dependency>

    <dependency>
        <groupId>org.postgresql</groupId>
        <artifactId>postgresql</artifactId>
        <version>42.7.3</version>
    </dependency>

    <!-- 可选：commons-lang3（字符串工具） -->
    <dependency>
        <groupId>org.apache.commons</groupId>
        <artifactId>commons-lang3</artifactId>
        <version>3.14.0</version>
    </dependency>
</dependencies>


# mysql
CREATE TABLE user (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50),
    age INT,
    create_time DATETIME
);

#pg
CREATE TABLE user (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    age INT,
    create_time TIMESTAMP
);
 */

import java.sql.*;
import java.util.ArrayList;
import java.util.List;

public class JdbcDemo {

    // ================== 🔧 MySQL 配置区 ==================
    private static final String URL = "jdbc:mysql://localhost:3306/test_db?useSSL=false&serverTimezone=UTC";
    private static final String USER = "root";
    private static final String PASSWORD = "123456";

    private static final String DRIVER = "com.mysql.cj.jdbc.Driver";
    // ==============================================

    // ================== 🔧 PostgreSQL 配置区 ==================
    private static final String URL = "jdbc:postgresql://localhost:5432/test_db";
    private static final String USER = "postgres";
    private static final String PASSWORD = "123456";

    private static final String DRIVER = "org.postgresql.Driver";
    // ========================================================

    public static void main(String[] args) throws Exception {
        // 1️⃣ 加载驱动
        Class.forName(DRIVER);
        // 2️⃣ 批量插入
        batchInsert();
        // 3️⃣ 查询数据
        queryData();
    }

    /**
     * 批量插入示例
     */
    public static void batchInsert() {
        String sql = "INSERT INTO user(name, age, create_time) VALUES (?, ?, ?)";

        List<Object[]> list = new ArrayList<>();
        list.add(new Object[]{"Alice", 20, LocalDateTime.now()});
        list.add(new Object[]{"Bob", 25, LocalDateTime.now()});
        list.add(new Object[]{"Charlie", 30, LocalDateTime.now()});

        try (Connection conn = DriverManager.getConnection(URL, USER, PASSWORD);
            PreparedStatement ps = conn.prepareStatement(sql)) {
            conn.setAutoCommit(false);
            for (Object[] obj : list) {
                ps.setString(1, (String) obj[0]);
                ps.setInt(2, (Integer) obj[1]);
                // ✅ 推荐写法（MySQL 8+）
                ps.setObject(3, obj[2]);
                ps.addBatch();
            }
            ps.executeBatch();
            conn.commit();
            System.out.println("✅ batch insert success");
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * 查询示例
     */
    public static void queryData() {
        String sql = "SELECT id, name, age FROM user";

        try (Connection conn = DriverManager.getConnection(URL, USER, PASSWORD);
             PreparedStatement ps = conn.prepareStatement(sql);
             ResultSet rs = ps.executeQuery()) {
            System.out.println("📌 Query result:");
            while (rs.next()) {
                int id = rs.getInt("id");
                String name = rs.getString("name");
                int age = rs.getInt("age");
                LocalDateTime time = getLocalDateTime(rs, "create_time");
                System.out.println(id + " | " + name + " | " + age + " | " + time);
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    /**
     * ✅ 统一时间转换（强烈推荐封装）
     */
    private static LocalDateTime getLocalDateTime(ResultSet rs, String column) throws SQLException {
        Object obj = rs.getObject(column);
        if (obj == null) {
            return null;
        }
        // MySQL 8+
        if (obj instanceof LocalDateTime) {
            return (LocalDateTime) obj;
        }
        // MySQL 5.x
        if (obj instanceof Timestamp) {
            return ((Timestamp) obj).toLocalDateTime();
        }
        throw new RuntimeException("Unsupported time type: " + obj.getClass());
    }
}