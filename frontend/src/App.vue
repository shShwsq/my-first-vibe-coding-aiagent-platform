<template>
  <ErrorBoundary>
    <router-view />
  </ErrorBoundary>
</template>

<script setup>
import ErrorBoundary from './components/ErrorBoundary.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #f5f7fa;
  overflow: hidden;
  overscroll-behavior: none;
}

html {
  overflow: hidden;
  overscroll-behavior: none;
}

.home-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon.agents {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.tests {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.success {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.runs {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-info h3 {
  font-size: 28px;
  color: #1a1a2e;
  margin-bottom: 4px;
}

.stat-info p {
  font-size: 14px;
  color: #666;
}

.welcome-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 16px;
  padding: 32px;
  color: #fff;
}

.welcome-card h2 {
  font-size: 24px;
  margin-bottom: 12px;
}

.welcome-card p {
  font-size: 16px;
  opacity: 0.9;
}

.coming-soon {
  background: #fff;
  border-radius: 16px;
  padding: 48px;
  text-align: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.coming-soon h2 {
  color: #1a1a2e;
  margin-bottom: 12px;
}

.coming-soon p {
  color: #666;
}
</style>
