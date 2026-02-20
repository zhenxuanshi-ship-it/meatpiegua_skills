#!/usr/bin/env node

/**
 * A股实时数据查询工具
 * 使用腾讯财经接口（无需认证）
 */

const http = require('http');

// 解析股票代码
function parseStockCode(code) {
  code = code.replace(/\s/g, '').toLowerCase();
  
  // 如果带后缀，直接返回
  if (code.startsWith('sh') || code.startsWith('sz') || code.startsWith('bj')) {
    return code;
  }
  
  // 根据代码规则判断交易所
  const prefix = code.substring(0, 3);
  
  if (['600', '601', '603', '605', '688', '689'].includes(prefix)) {
    return `sh${code}`;
  } else if (['000', '002', '003', '300', '301'].includes(prefix)) {
    return `sz${code}`;
  } else if (['430', '830', '87', '88', '89'].includes(prefix)) {
    return `bj${code}`;
  }
  
  // 默认深圳
  return `sz${code}`;
}

// 查询股票数据
function queryStock(codes) {
  return new Promise((resolve, reject) => {
    const stockList = codes.split(/[,，]/).map(c => parseStockCode(c.trim())).join(',');
    const url = `http://qt.gtimg.cn/q=${stockList}`;
    
    http.get(url, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          const results = parseResponse(data);
          resolve(results);
        } catch (err) {
          reject(new Error(`解析数据失败: ${err.message}`));
        }
      });
    }).on('error', (err) => {
      reject(new Error(`请求失败: ${err.message}`));
    }).setTimeout(10000, () => {
      reject(new Error('请求超时'));
    });
  });
}

// 解析腾讯返回数据
function parseResponse(data) {
  const results = [];
  const lines = data.split(';');
  
  for (const line of lines) {
    if (!line.trim() || !line.includes('=')) continue;
    
    // 匹配 v_code="数据";
    const match = line.match(/v_(\w+)="([^"]*)"/);
    if (!match) continue;
    
    const [, code, dataStr] = match;
    if (!dataStr) continue;
    
    const fields = dataStr.split('~');
    if (fields.length < 45) continue;
    
    // 腾讯数据格式：
    // 0:未知 1:名称 2:代码 3:当前价 4:昨收 5:今开
    // 6:成交量(手) 7:外盘 8:内盘
    // 9:买一价 10:买一量 11:买二价 12:买二量 ...
    // 19:卖一价 20:卖一量 21:卖二价 22:卖二量 ...
    // 33:最高价 34:最低价 35:最新价/收盘价
    // 36:成交量(手) 37:成交额(万) ...
    
    results.push({
      code: fields[2],
      name: fields[1],
      current: parseFloat(fields[3]),
      close: parseFloat(fields[4]),
      open: parseFloat(fields[5]),
      volume: parseInt(fields[6]),
      high: parseFloat(fields[33]),
      low: parseFloat(fields[34]),
      amount: parseFloat(fields[37]) * 10000, // 万转元
      buy1Price: parseFloat(fields[9]),
      buy1Volume: parseInt(fields[10]),
      sell1Price: parseFloat(fields[19]),
      sell1Volume: parseInt(fields[20]),
      change: parseFloat(fields[3]) - parseFloat(fields[4]),
      changePercent: parseFloat(fields[32])
    });
  }
  
  return results;
}

// 格式化输出
function formatOutput(stock) {
  const change = stock.change;
  const changePercent = stock.changePercent;
  const changeSymbol = change >= 0 ? '+' : '';
  const changeEmoji = change >= 0 ? '📈' : '📉';
  
  const volumeWan = (stock.volume / 100).toFixed(2); // 手转万股
  const amountYi = (stock.amount / 100000000).toFixed(2);
  const marketCapYi = ((stock.current * parseInt(stock.volume)) / 100000000).toFixed(2);
  
  return `📊 ${stock.name} (${stock.code}) ${changeEmoji}
━━━━━━━━━━━━━━━━━━━━━━
现价：${stock.current.toFixed(2)}元
涨跌：${changeSymbol}${change.toFixed(2)} (${changeSymbol}${changePercent.toFixed(2)}%)
今开：${stock.open.toFixed(2)}元
最高：${stock.high.toFixed(2)}元
最低：${stock.low.toFixed(2)}元
昨收：${stock.close.toFixed(2)}元
━━━━━━━━━━━━━━━━━━━━━━
成交量：${volumeWan}万手
成交额：${amountYi}亿元
━━━━━━━━━━━━━━━━━━━━━━
买一：${stock.buy1Price.toFixed(2)} (${stock.buy1Volume}手)
卖一：${stock.sell1Price.toFixed(2)} (${stock.sell1Volume}手)
━━━━━━━━━━━━━━━━━━━━━━
数据来源：腾讯财经 | 延迟约15分钟`;
}

// 主函数
async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.log('Usage: stock-query <股票代码1,股票代码2,...>');
    console.log('Example: stock-query 002340');
    console.log('Example: stock-query 002340,601857,300102');
    process.exit(1);
  }
  
  const codes = args[0];
  
  try {
    const results = await queryStock(codes);
    
    if (results.length === 0) {
      console.log('未找到股票数据');
      process.exit(1);
    }
    
    for (const stock of results) {
      console.log(formatOutput(stock));
      console.log('\n');
    }
  } catch (err) {
    console.error('查询失败:', err.message);
    process.exit(1);
  }
}

main();
