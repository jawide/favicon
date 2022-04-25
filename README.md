自动解析网站图标，并以跨域的方式代理该图标

## 使用例子

http://favicon.com/http://baidu.com 

```html
<img src="http://favicon.com/http://baidu.com"/>
```

## 流程图

```mermaid
graph LR
    url -- requests get --> dom
    dom -- parse --> link1[< link type='icon' href='...'/>]
    dom -- parse --> link2[< link type='shortcut'  href='...'/>]
    dom -- parse --> link3[< link type='...'  href='...'/>]
    url -- url + favicon.ico --> url_icon
    url -- domain + favicion.ico --> domain_icon
    link1 & link2 & link3 & url_icon & domain_icon --> icon_urls
    icon_urls -- select --> icon
```

## 部署

### 克隆代码
```bash
git clone https://github.com/jawide/favicon
```

### 使用docker-compose一键部署
```bash
docker-compose up -d
```