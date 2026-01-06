# listen rules

## 目录职责
- api：只写 HTTP 路由/参数校验/返回；禁止业务逻辑、文件存储、ASR、DB 操作
- application：只写用例/流程编排（上传→转写→保存→查询）；只依赖 interfaces
- interfaces：定义抽象接口与 DTO（Protocol/ABC/Pydantic）；不写任何实现
- infra：实现 interfaces（存储/ASR/Repo/队列）；不包含业务流程

## 依赖规则
- api -> application
- application -> interfaces
- infra -> interfaces
- 禁止：application import infra；api import infra

## 代码落点
- 新增功能：先加 interfaces，再写 infra 实现，最后在 application 编排，api 只调用 application
