<template>
  <div class="stock-list-page">
    <AppHeader />

    <!-- 页面级导航栏：返回主页 -->
    <div class="page-header">
      <div class="header-left">
        <router-link to="/" class="back-link">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 12H5M12 19l-7-7 7-7"/>
          </svg>
          返回主页
        </router-link>
        <span class="page-title">行情</span>
      </div>
    </div>

    <!-- 搜索栏 -->
    <div class="card search-bar" style="margin:12px 16px 0;">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索股票代码或名称"
        clearable
        @keyup.enter="handleSearch"
        style="max-width: 400px"
      >
        <template #append>
          <el-button @click="handleSearch">
            <el-icon><Search /></el-icon>
          </el-button>
        </template>
      </el-input>
    </div>

    <!-- 股票列表 -->
    <div class="card">
      <el-table
        :data="stocks"
        stripe
        @row-click="handleRowClick"
        style="cursor: pointer"
      >
        <el-table-column prop="code" label="代码" width="100" />
        <el-table-column prop="name" label="名称" min-width="120" />
        <el-table-column prop="market" label="市场" width="80">
          <template #default="{ row }">
            <el-tag size="small">
              {{ row.market?.toUpperCase() || 'N/A' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="industry" label="行业" min-width="120" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click.stop="viewDetail(row.code)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 搜索无结果提示 -->
      <div v-if="searchKeyword && total === 0 && !searchLoading" class="empty-result">
        <p class="empty-text">未找到 "<strong>{{ searchKeyword }}</strong>" 相关信息</p>
        <p class="empty-hint">预设列表和实时查询均无结果，您仍可直接查看详情页</p>
        <el-button type="primary" @click="viewDirectSearch(searchKeyword)">
          直接查看 {{ searchKeyword }} 行情
        </el-button>
      </div>

      <!-- 实时搜索中 -->
      <div v-if="searchLoading" class="search-loading">
        <span>正在实时搜索 "{{ searchKeyword }}" ...</span>
      </div>

      <el-pagination
        v-if="total > pageSize"
        :total="total"
        :page-size="pageSize"
        :current-page="currentPage"
        @current-change="handlePageChange"
        layout="prev, pager, next"
        style="margin-top: 16px; justify-content: center"
      />
    </div>
  </div>
</template>

<script setup>
/**
 * 行情列表页 - 预加载模式（内置股票数据，无需等待API）
 */
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppHeader from '@/components/AppHeader.vue'
import { stockApi } from '@/api'

const router = useRouter()

const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = 50

/** 实时搜索状态 */
const searchLoading = ref(false)
const apiResults = ref([])
const apiSearched = ref(false)

/** 预加载的A股热门股票列表（页面打开即显示，无需网络请求） */
const ALL_STOCKS = [
  { code: '000001', name: '平安银行', market: 'SZ', industry: '银行' },
  { code: '000002', name: '万科A', market: 'SZ', industry: '房地产' },
  { code: '000063', name: '中兴通讯', market: 'SZ', industry: '通信设备' },
  { code: '000100', name: 'TCL科技', market: 'SZ', industry: '电子' },
  { code: '000157', name: '中联重科', market: 'SZ', industry: '工程机械' },
  { code: '000333', name: '美的集团', market: 'SZ', industry: '家电' },
  { code: '000338', name: '潍柴动力', market: 'SZ', industry: '汽车零部件' },
  { code: '000425', name: '徐工机械', market: 'SZ', industry: '工程机械' },
  { code: '000538', name: '云南白药', market: 'SZ', industry: '医药生物' },
  { code: '000568', name: '泸州老窖', market: 'SZ', industry: '食品饮料' },
  { code: '000625', name: '长安汽车', market: 'SZ', industry: '汽车整车' },
  { code: '000651', name: '格力电器', market: 'SZ', industry: '家电' },
  { code: '000725', name: '京东方A', market: 'SZ', industry: '电子' },
  { code: '000768', name: '中航西飞', market: 'SZ', industry: '航空航天' },
  { code: '000776', name: '广发证券', market: 'SZ', industry: '证券' },
  { code: '000858', name: '五粮液', market: 'SZ', industry: '食品饮料' },
  { code: '000895', name: '双汇发展', market: 'SZ', industry: '食品饮料' },
  { code: '000938', name: '紫光股份', market: 'SZ', industry: '计算机' },
  { code: '001289', name: '龙源电力', market: 'SZ', industry: '电力及公用事业' },
  { code: '002007', name: '华兰生物', market: 'SZ', industry: '医药生物' },
  { code: '002027', name: '分众传媒', market: 'SZ', industry: '传媒' },
  { code: '002049', name: '紫光国微', market: 'SZ', industry: '电子' },
  { code: '002120', name: '韵达股份', market: 'SZ', industry: '交通运输' },
  { code: '002142', name: '宁波银行', market: 'SZ', industry: '银行' },
  { code: '002230', name: '科大讯飞', market: 'SZ', industry: '计算机' },
  { code: '002236', name: '大华股份', market: 'SZ', industry: '计算机' },
  { code: '002241', name: '歌尔股份', market: 'SZ', industry: '电子' },
  { code: '002304', name: '洋河股份', market: 'SZ', industry: '食品饮料' },
  { code: '002352', name: '顺丰控股', market: 'SZ', industry: '交通运输' },
  { code: '002371', name: '北方华创', market: 'SZ', industry: '半导体设备' },
  { code: '002415', name: '海康威视', market: 'SZ', industry: '计算机' },
  { code: '002475', name: '立讯精密', market: 'SZ', industry: '电子' },
  { code: '002493', name: '荣盛石化', market: 'SZ', industry: '石油化工' },
  { code: '002555', name: '三七互娱', market: 'SZ', industry: '传媒' },
  { code: '002594', name: '比亚迪', market: 'SZ', industry: '汽车整车' },
  { code: '002602', name: '世纪华通', market: 'SZ', industry: '传媒' },
  { code: '002714', name: '牧原股份', market: 'SZ', industry: '农林牧渔' },
  { code: '002812', name: '恩捷股份', market: 'SZ', industry: '新能源材料' },
  { code: '003816', name: '中国软件', market: 'SZ', industry: '计算机' },
  { code: '300001', name: '特锐德', market: 'SZ', industry: '电气设备' },
  { code: '300003', name: '乐普医疗', market: 'SZ', industry: '医疗器械' },
  { code: '300014', name: '亿纬锂能', market: 'SZ', industry: '电池' },
  { code: '300015', name: '爱尔眼科', market: 'SZ', industry: '医疗服务' },
  { code: '300033', name: '同花顺', market: 'SZ', industry: '计算机' },
  { code: '300059', name: '东方财富', market: 'SZ', industry: '证券' },
  { code: '300124', name: '汇川技术', market: 'SZ', industry: '工业自动化' },
  { code: '300142', name: '沃森生物', market: 'SZ', industry: '医药生物' },
  { code: '300223', name: '北京君正', market: 'SZ', industry: '半导体' },
  { code: '300274', name: '阳光电源', market: 'SZ', industry: '光伏设备' },
  { code: '300308', name: '中际旭创', market: 'SZ', industry: '通信设备' },
  { code: '300347', name: '泰格医药', market: 'SZ', industry: '医疗服务' },
  { code: '300394', name: '天孚通信', market: 'SZ', industry: '通信设备' },
  { code: '300408', name: '三环集团', market: 'SZ', industry: '电子元件' },
  { code: '300418', name: '昆仑万维', market: 'SZ', industry: '计算机' },
  { code: '300433', name: '蓝思科技', market: 'SZ', industry: '电子' },
  { code: '300432', name: '富瀚微', market: 'SZ', industry: '半导体' },
  { code: '300450', name: '先导智能', market: 'SZ', industry: '锂电设备' },
  { code: '300474', name: '景嘉微', market: 'SZ', industry: '半导体' },
  { code: '300496', name: '中科创达', market: 'SZ', industry: '计算机' },
  { code: '300502', name: '新易盛', market: 'SZ', industry: '通信设备' },
  { code: '300529', name: '健帆生物', market: 'SZ', industry: '医疗器械' },
  { code: '300661', name: '圣邦股份', market: 'SZ', industry: '模拟芯片设计' },
  { code: '300750', name: '宁德时代', market: 'SZ', industry: '电池' },
  { code: '300760', name: '迈瑞医疗', market: 'SZ', industry: '医疗器械' },
  { code: '300782', name: '卓胜微', market: 'SZ', industry: '射频芯片' },
  { code: '300832', name: '新产业', market: 'SZ', industry: '医疗器械' },
  { code: '300896', name: '爱美客', market: 'SZ', industry: '医美用品' },
  { code: '300900', name: '中辰欣荣', market: 'SZ', industry: '新材料' },
  { code: '300979', name: '华利集团', market: 'SZ', industry: '纺织服装' },
  { code: '301269', name: '华大九天', market: 'SZ', industry: 'EDA软件' },
  { code: '600009', name: '上海机场', market: 'SH', industry: '机场' },
  { code: '600010', name: '包钢股份', market: 'SH', industry: '钢铁' },
  { code: '600016', name: '民生银行', market: 'SH', industry: '银行' },
  { code: '600019', name: '宝钢股份', market: 'SH', industry: '钢铁' },
  { code: '600025', name: '华能水电', market: 'SH', industry: '电力' },
  { code: '600028', name: '中国石化', market: 'SH', industry: '石油石化' },
  { code: '600029', name: '南方航空', market: 'SH', industry: '航空运输' },
  { code: '600030', name: '中信证券', market: 'SH', industry: '证券' },
  { code: '600031', name: '三一重工', market: 'SH', industry: '工程机械' },
  { code: '600036', name: '招商银行', market: 'SH', industry: '银行' },
  { code: '600048', name: '保利发展', market: 'SH', industry: '房地产' },
  { code: '600050', name: '中国联通', market: 'SH', industry: '通信运营' },
  { code: '600061', name: '国投资本', market: 'SH', industry: '证券' },
  { code: '600085', name: '同仁堂', market: 'SH', industry: '中药' },
  { code: '600089', name: '特变电工', market: 'SH', industry: '光伏设备' },
  { code: '600104', name: '上汽集团', market: 'SH', industry: '汽车整车' },
  { code: '600111', name: '北方稀土', market: 'SH', industry: '稀土' },
  { code: '600115', name: '中国东航', market: 'SH', industry: '航空运输' },
  { code: '600150', name: '中国船舶', market: 'SH', industry: '船舶制造' },
  { code: '600176', name: '中国巨石', market: 'SH', industry: '玻纤' },
  { code: '600196', name: '复星医药', market: 'SH', industry: '医药生物' },
  { code: '600233', name: '圆通速递', market: 'SH', industry: '物流' },
  { code: '600256', name: '广汇能源', market: 'SH', industry: '煤炭' },
  { code: '600276', name: '恒瑞医药', market: 'SH', industry: '医药生物' },
  { code: '600309', name: '万华化学', market: 'SH', industry: '化学制品' },
  { code: '600346', name: '恒力石化', market: 'SH', industry: '石油化工' },
  { code: '600352', name: '浙江龙盛', market: 'SH', industry: '染料' },
  { code: '600372', name: '中航机载', market: 'SH', industry: '航空航天' },
  { code: '600383', name: '金山办公', market: 'SH', industry: '计算机' },
  { code: '600406', name: '国电南瑞', market: 'SH', industry: '电网设备' },
  { code: '600436', name: '片仔癀', market: 'SH', industry: '中药' },
  { code: '600438', name: '通威股份', market: 'SH', industry: '光伏设备' },
  { code: '600482', name: '中国动力', market: 'SH', industry: '船舶制造' },
  { code: '600489', name: '中金黄金', market: 'SH', industry: '贵金属' },
  { code: '600498', name: '烽火通信', market: 'SH', industry: '通信设备' },
  { code: '600519', name: '贵州茅台', market: 'SH', industry: '白酒' },
  { code: '600570', name: '恒生电子', market: 'SH', industry: '计算机' },
  { code: '600588', name: '用友网络', market: 'SH', industry: '计算机' },
  { code: '600585', name: '海螺水泥', market: 'SH', industry: '建材' },
  { code: '600598', name: '北大荒', market: 'SH', industry: '种植业' },
  { code: '600606', name: '绿地控股', market: 'SH', industry: '房地产' },
  { code: '600690', name: '海尔智家', market: 'SH', industry: '家电' },
  { code: '600745', name: '闻泰科技', market: 'SH', industry: '半导体' },
  { code: '600809', name: '山西汾酒', market: 'SH', industry: '白酒' },
  { code: '600837', name: '海通证券', market: 'SH', industry: '证券' },
  { code: '600859', name: '王府井', market: 'SH', industry: '商业零售' },
  { code: '600867', name: '通化东宝', market: 'SH', industry: '医药生物' },
  { code: '600886', name: '国投电力', market: 'SH', industry: '电力' },
  { code: '600887', name: '伊利股份', market: 'SH', industry: '乳品' },
  { code: '600893', name: '航发动力', market: 'SH', industry: '航空航天' },
  { code: '600900', name: '长江电力', market: 'SH', industry: '电力' },
  { code: '600919', name: '江苏银行', market: 'SH', industry: '银行' },
  { code: '600941', name: '中国移动', market: 'SH', industry: '通信运营' },
  { code: '600958', name: '东方证券', market: 'SH', industry: '证券' },
  { code: '601012', name: '隆基绿能', market: 'SH', industry: '光伏设备' },
  { code: '601066', name: '中信建投', market: 'SH', industry: '证券' },
  { code: '601088', name: '中国神华', market: 'SH', industry: '煤炭' },
  { code: '601111', name: '中国国航', market: 'SH', industry: '航空运输' },
  { code: '601127', name: '赛力斯', market: 'SH', industry: '汽车整车' },
  { code: '601138', name: '工业富联', market: 'SH', industry: '消费电子' },
  { code: '601166', name: '兴业银行', market: 'SH', industry: '银行' },
  { code: '601168', name: '西部矿业', market: 'SH', industry: '有色金属' },
  { code: '601177', name: '杭齿前进', market: 'SH', industry: '通用设备' },
  { code: '601186', name: '中国铁建', market: 'SH', industry: '基建工程' },
  { code: '601211', name: '国泰君安', market: 'SH', industry: '证券' },
  { code: '601225', name: '陕西煤业', market: 'SH', industry: '煤炭' },
  { code: '601228', name: '广州港', market: 'SH', industry: '港口航运' },
  { code: '601236', name: '红塔证券', market: 'SH', industry: '证券' },
  { code: '601288', name: '农业银行', market: 'SH', industry: '银行' },
  { code: '601318', name: '中国平安', market: 'SH', industry: '保险' },
  { code: '601328', name: '交通银行', market: 'SH', industry: '银行' },
  { code: '601360', name: '三六零', market: 'SH', industry: '网络安全' },
  { code: '601390', name: '中国中铁', market: 'SH', industry: '基建工程' },
  { code: '601398', name: '工商银行', market: 'SH', industry: '银行' },
  { code: '601618', name: '中国中冶', market: 'SH', industry: '基建工程' },
  { code: '601628', name: '中国人寿', market: 'SH', industry: '保险' },
  { code: '601633', name: '长城汽车', market: 'SH', industry: '汽车整车' },
  { code: '601665', name: '齐翔腾达', market: 'SH', industry: '化学原料' },
  { code: '601668', name: '中国建筑', market: 'SH', industry: '基建工程' },
  { code: '601669', name: '中国电建', market: 'SH', industry: '基建工程' },
  { code: '601688', name: '华泰证券', market: 'SH', industry: '证券' },
  { code: '601699', name: '潞安环能', market: 'SH', industry: '煤炭' },
  { code: '601728', name: '中国电信', market: 'SH', industry: '通信运营' },
  { code: '601766', name: '中国中车', market: 'SH', industry: '轨交装备' },
  { code: '601788', name: '光大证券', market: 'SH', industry: '证券' },
  { code: '601799', name: '星宇股份', market: 'SH', industry: '汽车零部件' },
  { code: '601800', name: '中国交建', market: 'SH', industry: '基建工程' },
  { code: '601816', name: '京沪高铁', market: 'SH', industry: '铁路运输' },
  { code: '601838', name: '成都银行', market: 'SH', industry: '银行' },
  { code: '601857', name: '中国石油', market: 'SH', industry: '石油石化' },
  { code: '601872', name: '招商轮船', market: 'SH', industry: '港口航运' },
  { code: '601877', name: '正泰电器', market: 'SH', industry: '电气设备' },
  { code: '601878', name: '浙商证券', market: 'SH', industry: '证券' },
  { code: '601888', name: '中国中免', market: 'SH', industry: '旅游零售' },
  { code: '601881', name: '中国银河', market: 'SH', industry: '证券' },
  { code: '601899', name: '紫金矿业', market: 'SH', industry: '有色金属' },
  { code: '601919', name: '中远海控', market: 'SH', industry: '港口航运' },
  { code: '601985', name: '中国核电', market: 'SH', industry: '核电' },
  { code: '601989', name: '中国人民保险', market: 'SH', industry: '保险' },
  { code: '601999', name: '出版传媒', market: 'SH', industry: '传媒' },
  { code: '603019', name: '中科曙光', market: 'SH', industry: '服务器' },
  { code: '603160', name: '汇顶科技', market: 'SH', industry: '芯片设计' },
  { code: '603259', name: '药明康德', market: 'SH', industry: 'CRO/CDMO' },
  { code: '603260', name: '合锻智能', market: 'SH', industry: '专用设备' },
  { code: '603290', name: '斯达半导', market: 'SH', industry: '功率半导体' },
  { code: '603501', name: '韦尔股份', market: 'SH', industry: '模拟芯片设计' },
  { code: '603799', name: '华友钴业', market: 'SH', industry: '有色金属' },
  { code: '603833', name: '欧派家居', market: 'SH', industry: '家具' },
  { code: '603899', name: '晨光股份', market: 'SH', industry: '文教休闲' },
  { code: '603920', name: '世运电路', market: 'SH', industry: 'PCB' },
  { code: '603986', name: '兆易创新', market: 'SH', industry: '存储器设计' },
  { code: '603993', name: '洛阳钼业', market: 'SH', industry: '有色金属' },
  { code: '688001', name: '华兴源创', market: 'SH', industry: '半导体检测' },
  { code: '688005', name: '容百科技', market: 'SH', industry: '锂电池材料' },
  { code: '688012', name: '中微公司', market: 'SH', industry: '半导体刻蚀' },
  { code: '688036', name: '传音控股', market: 'SH', industry: '消费电子' },
  { code: '688041', name: '海光信息', market: 'SH', industry: 'CPU/GPU' },
  { code: '688056', name: '莱特光电', market: 'SH', industry: 'OLED材料' },
  { code: '688099', name: '晶晨股份', market: 'SH', industry: 'SoC芯片' },
  { code: '688111', name: '金山云', market: 'SH', industry: '云计算' },
  { code: '688187', name: '时代电气', market: 'SH', industry: '轨道交通' },
  { code: '688256', name: '寒武纪', market: 'SH', industry: 'AI芯片' },
  { code: '688303', name: '大全能源', market: 'SH', industry: '硅料' },
  { code: '688396', name: '华润微', market: 'SH', industry: '功率半导体' },
  { code: '688498', name: '源杰科技', market: 'SH', industry: '光芯片' },
  { code: '688561', name: '奇安信', market: 'SH', industry: '网络安全' },
  { code: '688599', name: '天合光能', market: 'SH', industry: '光伏组件' },
  { code: '688772', name: '珠海冠宇', market: 'SH', industry: '电池' },
  { code: '688981', name: '中芯国际', market: 'SH', industry: '晶圆代工' },
]

/** 搜索过滤后的结果（纯客户端计算，无需请求） */
const filteredStocks = computed(() => {
  const kw = (searchKeyword.value || '').trim().toLowerCase()
  if (!kw) return ALL_STOCKS
  return ALL_STOCKS.filter(s =>
    s.code.includes(kw) || s.name.toLowerCase().includes(kw) || (s.industry || '').toLowerCase().includes(kw)
  )
})

/** 当前页数据：优先显示本地列表，本地无匹配时使用API搜索结果 */
const stocks = computed(() => {
  // 有API搜索结果时优先显示
  if (apiResults.value.length > 0) {
    const start = (currentPage.value - 1) * pageSize
    return apiResults.value.slice(start, start + pageSize)
  }
  const start = (currentPage.value - 1) * pageSize
  return filteredStocks.value.slice(start, start + pageSize)
})
const total = computed(() =>
  apiResults.value.length > 0 ? apiResults.value.length : filteredStocks.value.length
)

/**
 * 客户端搜索：本地列表优先，无匹配时自动调用后端API实时搜索
 */
const handleSearch = () => {
  currentPage.value = 1
  // 清除之前的API结果
  apiResults.value = []
  apiSearched.value = false

  const kw = (searchKeyword.value || '').trim()
  if (!kw) return

  // 本地列表中有匹配，无需API
  if (filteredStocks.value.length > 0) return

  // 本地无匹配 → 调用后端实时搜索
  fetchFromApi(kw)
}

/**
 * 后端API实时搜索股票
 * @param {string} keyword - 搜索关键词
 */
const fetchFromApi = async (keyword) => {
  searchLoading.value = true
  apiSearched.value = true
  try {
    const res = await stockApi.search(keyword)
    if (res && res.stocks && res.stocks.length > 0) {
      // 映射后端返回字段为展示格式
      apiResults.value = res.stocks.map(s => ({
        code: s.code,
        name: s.name,
        market: s.code?.startsWith('6') ? 'SH' : 'SZ',
        industry: s.industry || s.industry_name || ''
      }))
    } else {
      apiResults.value = []
    }
  } catch (e) {
    console.error('实时搜索失败:', e)
    apiResults.value = []
    ElMessage.warning('实时搜索失败，请稍后重试')
  } finally {
    searchLoading.value = false
  }
}

/** 分页切换 */
const handlePageChange = (page) => {
  currentPage.value = page
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

/** 点击行跳转详情 */
const handleRowClick = (row) => {
  router.push(`/stock/${row.code}`)
}
const viewDetail = (code) => {
  router.push(`/stock/${code}`)
}

/**
 * 搜索无匹配时，直接跳转到输入代码的行情详情页
 * @param {string} code - 用户输入的股票代码
 */
const viewDirectSearch = (code) => {
  const cleanCode = (code || '').trim()
  if (!cleanCode) return
  // 简单校验：A股代码为6位数字
  if (/^\d{6}$/.test(cleanCode)) {
    router.push(`/stock/${cleanCode}`)
  } else {
    // 非法格式提示
    ElMessage.warning('请输入正确的6位股票代码')
  }
}
</script>

<style scoped>
.stock-list-page {
  min-height: 100vh;
  padding: 16px 20px;
  box-sizing: border-box;
  max-width: 100%;
  overflow-y: auto;
}

/* ============ 页面顶部导航：简洁文字行 ============ */
.page-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.header-left { display: flex; align-items: center; gap: 12px; }

.back-link {
  position: relative;
  display: flex; align-items: center; gap: 6px;
  padding: 7px 14px;
  background: linear-gradient(180deg, #1e2535 0%, #151c2e 100%);
  border: 1px solid #2a3348;
  border-radius: 8px;
  color: #8b949e; text-decoration: none;
  font-size: 13px;
  box-shadow:
    0 2px 0 #0d1117,
    0 4px 8px rgba(0,0,0,0.3),
    inset 0 1px 0 rgba(255,255,255,0.04);
  transition: all 0.25s ease;
  overflow: hidden;
}
.back-link::before {
  content: '';
  position: absolute;
  top: 0; left: -100%;
  width: 60%; height: 100%;
  background: linear-gradient(90deg,
    transparent,
    rgba(88,166,255,0.06),
    rgba(88,166,255,0.12),
    rgba(88,166,255,0.06),
    transparent
  );
  animation: btnShimmer 3s ease-in-out infinite;
}
@keyframes btnShimmer {
  0%, 100% { left: -100%; }
  50% { left: 120%; }
}
.back-link:hover {
  background: linear-gradient(180deg, #253050 0%, #1a2540 100%);
  color: #58a6ff; border-color: #58a6ff;
  box-shadow:
    0 2px 0 #0d1829,
    0 6px 16px rgba(88,166,255,0.15),
    0 0 20px rgba(88,166,255,0.08),
    inset 0 1px 0 rgba(255,255,255,0.06);
  transform: translateY(-1px);
}
.back-link:active {
  transform: translateY(1px);
  box-shadow:
    0 1px 0 #0d1117,
    0 2px 4px rgba(0,0,0,0.3);
}
.page-title { font-size: 16px; font-weight: 600; color: var(--text-primary, #c9cdd4); }

.search-bar {
  display: flex;
  gap: 16px;
  align-items: center;
}

/* 搜索无结果提示 */
.empty-result {
  padding: 40px 20px;
  text-align: center;
}
.empty-text {
  font-size: 14px; color: var(--text-secondary, #8b949e);
  margin-bottom: 6px;
}
.empty-text strong { color: var(--text-primary, #c9cdd4); }
.empty-hint {
  font-size: 12px; color: var(--text-tertiary, #6a737d);
  margin-bottom: 16px;
}

/* 实时搜索加载中 */
.search-loading {
  padding: 40px 20px;
  text-align: center;
  color: var(--text-secondary, #8b949e);
  font-size: 14px;
  display: flex; align-items: center; justify-content: center; gap: 8px;
}
</style>
