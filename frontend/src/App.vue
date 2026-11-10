<template>
  <div class="app-shell">
    <aside class="sidebar" aria-label="主导航">
      <a class="brand" href="#overview" aria-label="轨迹实验室首页">
        <span class="brand-mark" aria-hidden="true"><i></i><i></i><i></i></span>
        <span><strong>轨迹实验室</strong><small>AGENT EVALUATION</small></span>
      </a>
      <div class="nav-caption">工作区</div>
      <nav class="nav-list">
        <a class="nav-item active" href="#overview"><span class="nav-glyph">▦</span>实验概览</a>
        <a class="nav-item" href="#run-config"><span class="nav-glyph">＋</span>运行实验</a>
        <a class="nav-item" href="#run-history"><span class="nav-glyph">≡</span>执行记录</a>
      </nav>
      <div class="sidebar-bottom">
        <div class="local-status"><span class="status-dot"></span><span>本地模拟环境<small>无需外部模型密钥</small></span></div>
        <div class="sidebar-foot">毕业设计 · 原型阶段</div>
      </div>
    </aside>

    <main class="main-content">
      <header class="topbar">
        <div class="breadcrumbs"><span>工作区</span><b>/</b><strong>实验概览</strong></div>
        <div class="topbar-meta"><span class="env-badge"><span class="status-dot"></span>LOCAL SANDBOX</span><el-button class="icon-button" aria-label="刷新数据" title="刷新数据" @click="refresh">↻</el-button></div>
      </header>

      <div class="page-wrap" id="overview">
        <section class="intro-row">
          <div>
            <p class="eyebrow">智能体工具调用 · 自动化评测</p>
            <h1>每次调用，都留下证据。</h1>
            <p class="intro-copy">在可控的工具环境中注入故障、观察执行轨迹，并量化恢复能力。</p>
          </div>
          <div class="intro-aside"><span class="pulse-ring"></span><span>评测引擎就绪<small>模拟器 v0.1 · 数据保存在本机</small></span></div>
        </section>

        <section class="metrics-grid" aria-label="评测指标">
          <article class="metric-cell"><span class="metric-label">累计执行</span><strong class="metric-value">{{ overview.total_runs }}</strong><span class="metric-note">最近 10000 条记录</span></article>
          <article class="metric-cell"><span class="metric-label">任务完成率</span><strong class="metric-value">{{ percent(overview.task_completion_rate) }}</strong><span class="metric-note">最终结果与预期一致</span></article>
          <article class="metric-cell"><span class="metric-label">故障恢复率</span><strong class="metric-value">{{ percent(overview.fault_recovery_rate) }}</strong><span class="metric-note">异常场景下成功恢复</span></article>
          <article class="metric-cell"><span class="metric-label">平均耗时</span><strong class="metric-value">{{ overview.average_execution_ms == null ? '—' : `${overview.average_execution_ms} ms` }}</strong><span class="metric-note">单次任务端到端耗时</span></article>
        </section>

        <section class="workspace-grid">
          <article class="panel run-panel" id="run-config">
            <div class="panel-heading"><div><span class="section-kicker">实验配置</span><h2>运行一次测试</h2></div><span class="panel-index">01</span></div>
            <el-form label-position="top" @submit.prevent="runOne">
              <el-form-item label="测试任务"><el-select v-model="form.task_id" aria-label="测试任务"><el-option v-for="task in tasks" :key="task.id" :label="task.title" :value="task.id" /></el-select></el-form-item>
              <el-form-item label="执行场景"><el-select v-model="form.scenario" aria-label="执行场景"><el-option v-for="scenario in scenarios" :key="scenario.id" :label="scenario.label" :value="scenario.id" /></el-select><p class="scenario-note">{{ currentScenario?.description }}</p></el-form-item>
              <el-form-item label="纠错策略"><el-select v-model="form.strategy" aria-label="纠错策略"><el-option v-for="(strategy, id) in strategies" :key="id" :label="strategy.label" :value="id" /></el-select></el-form-item>
              <el-form-item label="重复轮数"><el-input-number v-model="repetitions" aria-label="重复轮数" :min="1" :max="30" :disabled="busy" controls-position="right" /><p class="scenario-note">批次将对比两种策略，最多 30 轮</p></el-form-item>
              <el-button class="primary-button" :loading="busy" @click="runOne"><span>{{ busy ? '正在运行…' : '运行测试' }}</span><span aria-hidden="true">↗</span></el-button>
              <el-button class="secondary-button experiment-button" :loading="busy" @click="runExperiment">运行双策略重复对照 <span aria-hidden="true">{{ tasks.length }} 任务 × {{ scenarios.length }} 场景 × {{ repetitions }} 轮</span></el-button>
            </el-form>
            <div class="config-foot"><span class="status-square"></span>所有执行均使用可复现的模拟工具</div>
          </article>

          <article class="panel chart-panel">
            <div class="panel-heading"><div><span class="section-kicker">场景表现</span><h2>{{ latestExperiment ? '最近批次的故障场景表现' : '不同故障下的完成情况' }}</h2></div><el-select v-model="chartStrategy" aria-label="图表纠错策略" class="chart-filter"><el-option v-for="(strategy, id) in strategies" :key="id" :label="strategy.label" :value="id" /></el-select></div>
            <div ref="chartElement" class="scenario-chart" aria-label="各测试场景的任务完成率"></div>
            <table class="chart-data-table"><thead><tr><th>故障场景</th><th>任务完成率</th><th>样本数</th></tr></thead><tbody><tr v-for="row in chartRows" :key="row.id"><th>{{ row.label }}</th><td>{{ row.value == null ? '暂无数据' : `${row.value}%` }}</td><td>{{ row.samples }}</td></tr></tbody></table>
            <div class="chart-foot"><span><i class="legend-mark"></i>任务完成率</span><span>{{ latestExperiment ? `${latestExperiment.repetitions} 轮重复 · 每场景 ${tasks.length} × ${latestExperiment.repetitions} 个样本` : '完成重复实验后显示批次结果' }}</span></div>
          </article>
        </section>

        <section v-if="latestExperiment" class="panel experiment-panel">
          <div class="panel-heading"><div><span class="section-kicker">可复现的策略对照</span><h2>批次结果 · {{ latestExperiment.repetitions }} 轮重复</h2></div><div class="experiment-actions"><span class="batch-id">{{ latestExperiment.id }}</span><el-button link @click="exportExperiment">导出批次报告</el-button></div></div>
          <div class="experiment-summary"><span>执行数 <strong>{{ latestExperiment.total_runs }}</strong></span><span>任务数 <strong>{{ tasks.length }}</strong></span><span>场景数 <strong>{{ scenarios.length }}</strong></span><span>策略数 <strong>{{ latestExperiment.strategies.length }}</strong></span></div>
          <div class="history-table-wrap"><el-table :data="experimentRows" empty-text="暂无策略对照结果。" size="small">
            <el-table-column prop="strategy_label" label="策略" min-width="130" />
            <el-table-column label="工具选择准确率" min-width="145"><template #default="scope">{{ metricPercent(scope.row.metrics.tool_selection_accuracy) }} <small class="sample-count">n={{ scope.row.metrics.tool_selection_sample_count }}</small></template></el-table-column>
            <el-table-column label="参数正确率" min-width="125"><template #default="scope">{{ metricPercent(scope.row.metrics.parameter_correctness) }} <small class="sample-count">n={{ scope.row.metrics.parameter_sample_count }}</small></template></el-table-column>
            <el-table-column label="任务完成率" min-width="125"><template #default="scope">{{ metricPercent(scope.row.metrics.task_completion_rate) }} <small class="sample-count">n={{ scope.row.metrics.task_completion_sample_count }}</small></template></el-table-column>
            <el-table-column label="故障恢复率" min-width="125"><template #default="scope">{{ metricPercent(scope.row.metrics.fault_recovery_rate) }} <small class="sample-count">n={{ scope.row.metrics.fault_recovery_sample_count }}</small></template></el-table-column>
            <el-table-column label="平均耗时" min-width="115"><template #default="scope">{{ metricDuration(scope.row.metrics.average_execution_ms) }}</template></el-table-column>
          </el-table></div>
        </section>

        <section v-if="experiments.length" class="panel experiment-history-panel">
          <div class="panel-heading"><div><span class="section-kicker">批次追踪</span><h2>实验历史</h2></div></div>
          <div class="history-table-wrap"><el-table :data="experiments.slice(0, 10)" empty-text="暂无实验批次。" size="small">
            <el-table-column label="创建时间" min-width="190"><template #default="scope">{{ formatDate(scope.row.created_at) }}</template></el-table-column>
            <el-table-column label="重复轮数" width="100"><template #default="scope">{{ scope.row.repetitions }}</template></el-table-column>
            <el-table-column label="策略" min-width="170"><template #default="scope">{{ scope.row.strategies.map((id) => strategies[id]?.label || id).join(' / ') }}</template></el-table-column>
            <el-table-column prop="total_runs" label="执行数" width="90" />
            <el-table-column label="" width="90"><template #default="scope"><el-button link @click="selectExperiment(scope.row)">查看报告</el-button></template></el-table-column>
          </el-table></div>
        </section>

        <section class="panel trace-panel" id="latest-panel">
          <div class="panel-heading trace-heading"><div><span class="section-kicker">最近的执行轨迹</span><h2>{{ latest ? `${latest.task_title} · ${scenarioName(latest.scenario)}` : '还没有执行记录' }}</h2></div><div class="trace-actions"><span class="run-result" :class="latest?.success ? 'good' : latest ? 'bad' : ''">{{ latest ? (latest.success ? (latest.recovered ? '故障已恢复' : '执行成功') : '执行失败') : '等待实验' }}</span><el-button link :disabled="!latest" @click="exportLatest">导出记录</el-button></div></div>
          <div v-if="latest" class="diagnosis-box"><span><strong>诊断结论：</strong>{{ latest.diagnosis.category }}</span><span><strong>执行证据：</strong>{{ latest.diagnosis.evidence }}</span><span><strong>改进建议：</strong>{{ latest.diagnosis.suggestion }}</span></div>
          <div class="trace-table-wrap"><el-table :data="latest?.trace || []" empty-text="运行一项测试后，这里会显示逐步执行证据。" size="small">
            <el-table-column label="调用" width="85"><template #default="scope"><span class="mono-cell">第 {{ scope.row.attempt }} 次</span></template></el-table-column>
            <el-table-column prop="tool" label="工具" min-width="130"><template #default="scope"><span class="mono-cell">{{ scope.row.tool }}</span></template></el-table-column>
            <el-table-column label="参数" min-width="170"><template #default="scope"><span class="mono-cell">{{ formatValue(scope.row.arguments) }}</span></template></el-table-column>
            <el-table-column label="返回 / 错误" min-width="160"><template #default="scope">{{ scope.row.message || formatValue(scope.row.result) }}</template></el-table-column>
            <el-table-column label="状态" width="125"><template #default="scope"><span class="status-pill" :class="scope.row.status === 'success' ? '' : 'failed'">{{ statusLabels[scope.row.status] || scope.row.status }}</span></template></el-table-column>
            <el-table-column label="耗时" width="100"><template #default="scope"><span class="mono-cell">{{ scope.row.duration_ms }} ms</span></template></el-table-column>
          </el-table></div>
        </section>

        <section class="panel history-panel" id="run-history">
          <div class="panel-heading"><div><span class="section-kicker">可追溯与可复现</span><h2>执行记录</h2></div><el-button link @click="exportRuns">导出最近记录</el-button></div>
          <div class="history-table-wrap"><el-table :data="runs.slice(0, 30)" empty-text="还没有执行记录。可以从左侧配置开始运行一个模拟测试。" size="small">
            <el-table-column prop="task_title" label="任务" min-width="150" />
            <el-table-column label="场景" min-width="120"><template #default="scope">{{ scenarioName(scope.row.scenario) }}</template></el-table-column>
            <el-table-column prop="strategy_label" label="策略" min-width="110" />
            <el-table-column label="结果" min-width="110"><template #default="scope">{{ scope.row.success ? (scope.row.recovered ? '故障已恢复' : '成功') : '失败' }}</template></el-table-column>
            <el-table-column label="诊断" min-width="130"><template #default="scope">{{ scope.row.diagnosis.category }}</template></el-table-column>
            <el-table-column label="耗时" width="100"><template #default="scope"><span class="mono-cell">{{ scope.row.execution_ms }} ms</span></template></el-table-column>
            <el-table-column label="" width="75"><template #default="scope"><el-button link @click="showRun(scope.row)">查看</el-button></template></el-table-column>
          </el-table></div>
        </section>
        <footer class="page-footer"><span>轨迹实验室 · 本地原型</span><span>实验数据为规则模拟，不代表真实大语言模型性能</span></footer>
      </div>
    </main>
  </div>
  <el-alert v-if="message" :title="message.text" :type="message.type" :closable="false" class="toast-message" />
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { BarChart } from 'echarts/charts';
import { GridComponent, TooltipComponent } from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';
import * as echarts from 'echarts/core';

echarts.use([BarChart, GridComponent, TooltipComponent, CanvasRenderer]);

const tasks = ref([]);
const scenarios = ref([]);
const strategies = ref({});
const runs = ref([]);
const experiments = ref([]);
const overview = reactive({ total_runs: 0, tool_selection_accuracy: null, parameter_correctness: null, task_completion_rate: null, fault_recovery_rate: null, average_execution_ms: null, invalid_call_rate: null });
const form = reactive({ task_id: '', scenario: 'normal', strategy: 'self_correcting' });
const repetitions = ref(3);
const chartStrategy = ref('self_correcting');
const latest = ref(null);
const latestExperiment = ref(null);
const busy = ref(false);
const message = ref(null);
const chartElement = ref(null);
let chart;
const statusLabels = { success: '成功', timeout: '超时', empty_result: '空结果', invalid_params: '参数错误', execution_failure: '执行失败', tool_selection_error: '工具选错' };
const currentScenario = computed(() => scenarios.value.find((item) => item.id === form.scenario));
const chartRows = computed(() => scenarios.value.filter((item) => item.id !== 'normal').map((scenario) => {
  const batchMetrics = latestExperiment.value?.scenario_metrics_by_strategy?.[chartStrategy.value]?.[scenario.id];
  const selected = runs.value.filter((run) => run.strategy === chartStrategy.value && run.scenario === scenario.id);
  return {
    id: scenario.id,
    label: scenario.label,
    value: batchMetrics
      ? (batchMetrics.task_completion_rate == null ? null : Math.round(batchMetrics.task_completion_rate * 100))
      : (selected.length ? Math.round(selected.filter((run) => run.success).length / selected.length * 100) : null),
    samples: batchMetrics?.task_completion_sample_count ?? selected.length,
  };
}));
const experimentRows = computed(() => (latestExperiment.value?.strategies || []).map((strategy) => ({
  strategy_label: strategies.value[strategy]?.label || strategy,
  metrics: latestExperiment.value.metrics_by_strategy[strategy],
})));

function percent(value) { return value == null ? '—' : `${Math.round(value * 100)}%`; }
function metricPercent(value) { return value == null ? '—' : `${(value * 100).toFixed(1)}%`; }
function metricDuration(value) { return value == null ? '—' : `${value} ms`; }
function formatDate(value) { return new Date(value).toLocaleString(); }
function scenarioName(id) { return scenarios.value.find((item) => item.id === id)?.label || id; }
function formatValue(value) { return value == null ? '—' : typeof value === 'object' ? JSON.stringify(value) : String(value); }

async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { 'Content-Type': 'application/json', ...(options.headers || {}) } });
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || data.error || `请求失败 (${response.status})`);
  return data;
}

function showMessage(text, type = 'success') {
  message.value = { text, type };
  window.clearTimeout(showMessage.timer);
  showMessage.timer = window.setTimeout(() => { message.value = null; }, 2800);
}

async function loadData() {
  const [taskData, metrics, runData, experimentData] = await Promise.all([api('/api/tasks'), api('/api/overview'), api('/api/runs'), api('/api/experiments')]);
  tasks.value = taskData.tasks;
  scenarios.value = taskData.scenarios;
  strategies.value = taskData.strategies;
  Object.assign(overview, metrics);
  runs.value = runData.runs;
  experiments.value = experimentData.experiments;
  latestExperiment.value = experiments.value[0] || null;
  if (!form.task_id && tasks.value.length) form.task_id = tasks.value[0].id;
  updateChart();
}

async function refresh() {
  try { await loadData(); showMessage('数据已刷新'); } catch (error) { showMessage(error.message, 'error'); }
}

async function runOne() {
  if (busy.value) return;
  busy.value = true;
  try {
    const data = await api('/api/run', { method: 'POST', body: JSON.stringify(form) });
    latest.value = data.run;
    await loadData();
    showMessage(data.run.success ? (data.run.recovered ? '测试完成，故障已恢复' : '测试执行成功') : '测试结束，请查看故障诊断', data.run.success ? 'success' : 'warning');
  } catch (error) { showMessage(error.message, 'error'); } finally { busy.value = false; }
}

async function runExperiment() {
  if (busy.value) return;
  busy.value = true;
  try {
    const data = await api('/api/experiments', { method: 'POST', body: JSON.stringify({ repetitions: repetitions.value }) });
    latestExperiment.value = data.experiment;
    latest.value = data.runs.at(-1) || null;
    await loadData();
    showMessage(`双策略重复实验完成：${data.experiment.total_runs} 次执行`);
  } catch (error) { showMessage(error.message, 'error'); } finally { busy.value = false; }
}

function updateChart() {
  if (!chart || !chartElement.value) return;
  const definitions = scenarios.value.filter((item) => item.id !== 'normal');
  const batchMetrics = latestExperiment.value?.scenario_metrics_by_strategy?.[chartStrategy.value];
  const selected = runs.value.filter((run) => run.strategy === chartStrategy.value);
  const values = definitions.map((scenario) => {
    if (batchMetrics?.[scenario.id]) {
      const rate = batchMetrics[scenario.id].task_completion_rate;
      return rate == null ? null : Math.round(rate * 100);
    }
    const subset = selected.filter((run) => run.scenario === scenario.id);
    return subset.length ? Math.round(subset.filter((run) => run.success).length / subset.length * 100) : null;
  });
  chart.setOption({
    animation: false,
    grid: { left: 83, right: 43, top: 8, bottom: 5 },
    xAxis: { type: 'value', min: 0, max: 100, axisLabel: { color: '#778b8d', fontSize: 9, formatter: '{value}%' }, axisLine: { show: false }, axisTick: { show: false }, splitLine: { lineStyle: { color: 'rgba(116, 153, 151, .18)', width: 1 } } },
    yAxis: { type: 'category', inverse: true, data: definitions.map((item) => item.label), axisLabel: { color: '#526b70', fontSize: 10 }, axisLine: { show: false }, axisTick: { show: false } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, valueFormatter: (value) => value == null ? '暂无数据' : `${value}%` },
    series: [{ name: '任务完成率', type: 'bar', barWidth: 8, data: values, itemStyle: { color: '#138f89', borderRadius: [0, 4, 4, 0] }, label: { show: true, position: 'right', color: '#42686a', fontSize: 9, formatter: ({ value }) => value == null ? '—' : `${value}%` }, emphasis: { focus: 'series' } }],
  }, true);
}

function download(filename, data) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function exportLatest() { if (latest.value) download(`trajectory-${latest.value.id}.json`, latest.value); }
function exportRuns() { download('agent-evaluation-runs.json', runs.value); }
async function exportExperiment() {
  if (!latestExperiment.value) return;
  try {
    const data = await api(`/api/experiments/${latestExperiment.value.id}`);
    download(`agent-evaluation-experiment-${latestExperiment.value.id}.json`, data);
  } catch (error) { showMessage(error.message, 'error'); }
}
async function selectExperiment(experiment) {
  try {
    const data = await api(`/api/experiments/${experiment.id}`);
    latestExperiment.value = data.experiment;
    latest.value = data.runs.at(-1) || latest.value;
    updateChart();
    showMessage('已载入实验批次报告');
  } catch (error) { showMessage(error.message, 'error'); }
}
function showRun(run) { latest.value = run; document.querySelector('#latest-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' }); }

function resizeChart() { chart?.resize(); }

watch(chartStrategy, updateChart);
watch(runs, updateChart, { deep: true });
watch(latestExperiment, updateChart, { deep: true });
onMounted(async () => {
  try {
    await loadData();
    await nextTick();
    chart = echarts.init(chartElement.value);
    updateChart();
    window.addEventListener('resize', resizeChart);
  } catch (error) { showMessage(`初始化失败：${error.message}`, 'error'); }
});
onBeforeUnmount(() => { window.removeEventListener('resize', resizeChart); chart?.dispose(); });
</script>
