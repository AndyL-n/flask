# 关键参数（请替换为实际 Secret，此处仅为演示）
import base64
import hashlib
import hmac

from botocore.utils import percent_encode

access_key_secret = "iyLQROV0q09ed8opxKqD38vFUYFDCJ"
string_to_sign = "GET&%2F&AccessKeyId%3DLTAI5t6DCywZWimWrDu4A67x%26Action%3DQueryDevicePropertyStatus%26DeviceName%3D240625-07%26Format%3DJSON%26ProductKey%3Dk1wixAHIHEl%26RegionId%3Dcn-shanghai%26SignatureMethod%3DHMAC-SHA1%26SignatureNonce%3D123475656%26SignatureVersion%3D1.0%26Timestamp%3D2025-06-27T12%253A12%253A24Z%26Version%3D2018-01-20"
# 构造签名密钥（AccessKeySecret + &）
key = f"{access_key_secret}&".encode("utf-8")
message = string_to_sign.encode("utf-8")

# 计算 HMAC-SHA1 哈希
hmac_sha1 = hmac.new(key, message, hashlib.sha1).digest()

# Base64 编码得到签名值
signature = base64.b64encode(hmac_sha1).decode("utf-8")
print("原始签名值：", signature)

signed_signature = percent_encode(signature)
print("URL 编码后签名：", signed_signature)