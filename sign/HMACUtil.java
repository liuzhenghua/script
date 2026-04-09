import java.util.Base64;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

class HMACUtil {

    /**
     * 这里需要注意如果你的http客户端会对query参数encode的话，这里就不能url encode了。
     */
    public static String hmac_sha256(String key, String data) {
        try {
            javax.crypto.Mac mac = javax.crypto.Mac.getInstance("HmacSHA256");
            mac.init(new javax.crypto.spec.SecretKeySpec(key.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
            byte[] hmacBytes = mac.doFinal(data.getBytes(StandardCharsets.UTF_8));

            // Base64 URL-safe 编码 (保留 padding 与 Python 一致)
            String base64Encoded = Base64.getUrlEncoder().encodeToString(hmacBytes);
            // URL 编码
            return URLEncoder.encode(base64Encoded, StandardCharsets.UTF_8.toString());
        } catch (NoSuchAlgorithmException | InvalidKeyException | java.io.UnsupportedEncodingException e) {
            log.error("Failed to generate sign", e);
            return "";
        }
    }
}