<template>
  <view class="page">
    <view class="header">
      <view class="h1">摘要结果</view>
      <view class="sub">elder_id: {{ elderId }} ｜ date: {{ date }}</view>
    </view>

    <view v-if="loading" class="tip">加载中...</view>
    <view v-else-if="error" class="error">请求失败：{{ error }}</view>

    <view v-else>
      <view class="card">
        <view class="title">返回状态</view>
        <text class="content pre">{{ detail.message }}</text>
      </view>

      <view class="card">
        <view class="title">summary</view>
        <text class="content pre">{{ detail.summary }}</text>
      </view>

      <view class="card">
        <view class="title">physical_status</view>
        <text class="content pre">{{ detail.physical_status }}</text>
      </view>

      <view class="card">
        <view class="title">psychological_needs</view>
        <text class="content pre">{{ detail.psychological_needs }}</text>
      </view>

      <view class="card">
        <view class="title">advice</view>
        <text class="content pre">{{ detail.advice }}</text>
      </view>

      <button class="btn" @click="fetchSummary">刷新</button>
    </view>
  </view>
</template>

<script>
export default {
  data() {
    return {
      baseUrl: "http://127.0.0.1:8000", // ✅ 改成你的后端地址（真机通常要 https 域名）
      elderId: 123,
      date: "2026-01-06",
      force: false,

      loading: false,
      error: "",
      detail: {
        elder_id: 0,
        date: "",
        summary: "",
        physical_status: "",
        psychological_needs: "",
        advice: "",
        message: ""
      }
    };
  },

  onLoad(options) {
    // 支持从路由参数带入：/pages/summary/summary?elder_id=123&date=2026-01-06
    if (options.elder_id) this.elderId = Number(options.elder_id);
    if (options.date) this.date = options.date;
    if (typeof options.force !== "undefined") this.force = options.force === "true";

    this.fetchSummary();
  },

  methods: {
    fetchSummary() {
      this.loading = true;
      this.error = "";

      uni.request({
        url: `${this.baseUrl}/parse/summary`,
        method: "GET", // 如果你接口是 POST，这里改成 "POST"
        data: {
          elder_id: this.elderId,
          date: this.date,
          force: this.force
        },
        timeout: 15000,

        success: (res) => {
          if (res.statusCode !== 200) {
            this.error = `HTTP ${res.statusCode}`;
            return;
          }

          // 你的后端已经保证稳定包含 summary 字段，这里直接接即可
          this.detail = {
            ...this.detail,
            ...res.data
          };
        },

        fail: (err) => {
          this.error = err.errMsg || String(err);
        },

        complete: () => {
          this.loading = false;
        }
      });
    }
  }
};
</script>

<style>
.page { padding: 16px; }
.header { margin-bottom: 12px; }
.h1 { font-size: 18px; font-weight: 700; }
.sub { font-size: 12px; color: #666; margin-top: 4px; }

.tip { padding: 12px; color: #666; }
.error { padding: 12px; color: #d00; }

.card {
  background: #fff;
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.06);
}

.title { font-weight: 700; margin-bottom: 8px; }
.content { font-size: 14px; line-height: 22px; color: #222; }

/* 关键：保留 \n 换行 */
.pre { white-space: pre-wrap; word-break: break-all; }

.btn { margin-top: 8px; }
</style>
