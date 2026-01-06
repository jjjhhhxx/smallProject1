🧪 测试方式
测试上传接口
# 使用 curl（PowerShell）
curl.exe -X POST "http://localhost:8000/listen/upload" 
 -F "elder_id=123" 
 -F "audio_file=@test.wav"

 
测试查询接口
curl.exe "http://localhost:8000/listen/records?elder_id=123&limit=20"