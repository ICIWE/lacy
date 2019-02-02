'use strict';

function GetQueryString(name) {
    var re = new RegExp('[\?&]' + name + '=([^&]*)(&|$)*', 'i');
    var r = window.location.search.match(re)

    // unescape(r[1])
    if (r != null) {return r[1];} else {return null;}
}

var page = GetQueryString('page') || '1',
    serialized = GetQueryString('serialized') || '',
    tv_type = GetQueryString('tv_type') || '',
    country = GetQueryString('country') || '',
    year = GetQueryString('year') || '';
var queryString = {
    page: page,
    serialized: serialized,
    tv_type: tv_type,
    country: country,
    year: year
};
function _query(kwargs){
    kwargs = $.extend({}, queryString, kwargs);
    location.href = `/category?page=${kwargs.page}&serialized=${kwargs.serialized}&tv_type=${kwargs.tv_type}&country=${kwargs.country}&year=${kwargs.year}`
}

// 搜索
function checkForm(){
    var form = document.getElementById('nav-search');
    var key = document.getElementById('nav-search-box').value;
    if (key === '' || key === undefined) {
        return false;
    } else {
        // window.location.href = '/search?key=' + key;
        return true;
    }
}

// 侧边栏- 显示/隐藏清单
function sidebarHead1SlideToggle() {
    var mylist = $('.mylist').first();
    if (mylist.css('display') === 'none') {
        mylist.show(200);
    } else {
        mylist.hide(200);
    }
}

function sidebarHead2SlideToggle() {
    var mycollection = $('.mycollection').first();
    if (mycollection.css('display') === 'none') {
        mycollection.show(200);
    } else {
        mycollection.hide(200);
    }
}

// pop
var pop_is_hide = 1;
var POP = {};

// pop // 新建清单：确认/取消
function createMyList() {
    var pop_w = $('.pop-up-window').first();
    var cml_w = $('.create-my-list').first();
    cml_w.css('visibility', 'visible');
    pop_w.css('visibility', 'visible');
}
function cmlCancel() {
    var title = $('#createListValue');
    var pop_w = $('.pop-up-window').first();
    var cml_w = $('.create-my-list').first();
    cml_w.css('visibility', 'hidden');

    var atl_w = $('.add-to-list').first();
    if (atl_w.css('visibility') === 'visible') {
        atl_w.css('background-color', '#fff')
    } else {
        pop_w.css('visibility', 'hidden');
    }

    title.val('');
}

function flashflash(p) {
    var _old = p.css('color');
    p.animate({
        opacity: 0
    }, 200).delay(100).animate({
        opacity: 1
    }).delay(100).animate({
        opacity: 0
    }, 200).delay(100).animate({
        opacity: 1
    })
}
function cmlConfirm() {
    var title = $('#createListValue');
    var pop_w = $('.pop-up-window').first();
    var cml_w = $('.create-my-list').first();
    var cmlalert = $('#cmlAlert')
    var re = /^\d+$/;
    var tv_id;
    if (POP.tv_id === undefined) {
        tv_id = '';
    } else if (re.test(POP.tv_id)) {
        tv_id = POP.tv_id;
    } else {
        tv_id = '';
    }

    if (title.val().length > 15 || title.val().length < 1) {
        flashflash(cmlalert);
        return;
    }

    window.location.href = `/collectionCreate/${title.val()}?tv_id=${tv_id}`

    cml_w.css('visibility', 'hidden');

    var atl_w = $('.add-to-list').first();
    if (atl_w.css('visibility') === 'visible') {
        atl_w.css('background-color', '#fff')

    } 
    pop_w.css('visibility', 'hidden');
    atl_w.css('visibility', 'hidden');
    title.val('');
}

// pop // 添加至清单
var re = /^\d+$/;
var atlList = $('.atl-list').first();
atlList.click(function(e) {
    var cId = e.target.getAttribute('data-id');
    if (cId === 'new') {
        var pop_w = $('.pop-up-window').first();
        var cml_w = $('.create-my-list').first();
        var atl_w = $('.add-to-list').first();
        atl_w.css('background-color', '#eee')
        cml_w.css('visibility', 'visible');
        pop_w.css('visibility', 'visible');
    } else if (re.test(cId)) {
        // 提交 cID 和 tv id;
        var para = {
            c_id: cId,
            tv_id: POP.tv_id
        };

        var data = JSON.stringify(para);
        var xhr = new XMLHttpRequest();
        xhr.open('POST', '/j/collection/item');
        xhr.setRequestHeader('Content-type', 'application/json');
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var response = JSON.parse(xhr.response);
                if (!response) {
                    infoPop('传送错误！');
                }
                if (response.code === 0) {
                    window.location.reload();
                    infoPop('添加成功！');
                } else {
                    infoPop(response.message);
                }

            }
        }
        xhr.send(data);

    } else {
        infoPop('数据错误！');
        return
    }
})

function atlOpenCollection(tv_id){
    var pop_w = $('.pop-up-window').first();
    var atl_w = $('.add-to-list').first();
    atl_w.css('visibility', 'visible');
    pop_w.css('visibility', 'visible');
    POP.tv_id = tv_id;
}

function atlCancel() {
    var pop_w = $('.pop-up-window').first();
    var atl_w = $('.add-to-list').first();
    pop_w.css('visibility', 'hidden');
    atl_w.css('visibility', 'hidden');
}

// 从清单删除
function removeFromCollection(cId, tvId) {
        var para = {
            c_id: cId,
            tv_id: tvId
        };

        var data = JSON.stringify(para);
        var xhr = new XMLHttpRequest();
        xhr.open('DELETE', '/j/collection/item');
        xhr.setRequestHeader('Content-type', 'application/json');
        xhr.onreadystatechange = function() {
            if (xhr.readyState === 4 && xhr.status === 200) {
                var response = JSON.parse(xhr.response);
                if (!response) {
                    infoPop('传送错误！');
                }
                if (response.code === 0) {
                    window.location.reload();
                    infoPop('删除成功！');
                } else {
                    infoPop(response.message);
                }

            }
        }
        xhr.send(data);
}
// 所有页面，加载完绑定事件 ----------------------------------------------


// timeline.htnl
// 时间轴函数
var weekMap = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
// HTML加载完执行
window.onload = function() {
    if (window.location.pathname === "/timeline") {
        function handler() {
            if (this.status === 200 && this.response != null) {
                var data = this.response;
                var headList = document.getElementsByClassName('th-date-list')[0];
                var bodyList = document.getElementsByClassName('tw-body-list')[0];

                // header
                if (data.code != 0) {
                    return
                }
                var r = data.result
                for (var i = 0; i < data.result.length; i++) {
                    var headDiv = document.createElement('div');

                    headDiv.setAttribute('class', 'th-head');
                    var span1 = document.createElement('span');
                    var span2 = document.createElement('span');
                    span1.setAttribute('class', 't-date');
                    span2.setAttribute('class', 't-week');
                    span1.innerText = r[i].date + '日';
                    span2.innerText = weekMap[r[i].day_of_week];
                    headDiv.appendChild(span1);
                    headDiv.appendChild(span2);

                    headList.appendChild(headDiv);

                    var columnDiv = document.createElement('div');
                    columnDiv.setAttribute('class', 'tw-column');
                    bodyList.appendChild(columnDiv);

                    if (r[i].items.length === 0) {
                        var itemDiv = document.createElement('div');
                        itemDiv.setAttribute('class', 'tw-item');
                        itemDiv.innerText = '本日无更新';
                        columnDiv.appendChild(itemDiv);
                        continue;
                    }
                    for (var j = 0; j < r[i].items.length; j++) {
                        var itemDiv = document.createElement('div');
                        var item = r[i].items[j];
                        var columnHtml = `
                            <div class="tw-img">
                                <a href="${item.url}" target="_blank">
                                    <img src="/static/${item.cover}">
                                </a>
                            </div>
                            <div class="tw-txt">
                                <a href="${item.url}" target="_blank">
                                    <p class="tw-p1">${item.name}</p>
                                </a>
                                <p class="tw-p2">第${item.last_ep + 1}集</p>
                            </div>`;
                        itemDiv.setAttribute('class', 'tw-item');
                        itemDiv.innerHTML = columnHtml;
                        columnDiv.appendChild(itemDiv);                
                    }
                }
            } else {
                infoPop('请求出错！');
            }    
        }

        var request = new XMLHttpRequest();

        request.onload = handler;
        request.responseType = 'json'
        request.open('GET', '/j/timeline')
        request.send();
    

        // 时间轴左右移动
        var arrowLeft = document.getElementsByClassName('th-arrow-left')[0];
        var arrowRight = document.getElementsByClassName('th-arrow-right')[0];

        var dateList = document.getElementsByClassName('th-date-list')[0];
        var bodyList = document.getElementsByClassName('tw-body-list')[0];

        var transform = -1500;
        function moveLeft() {
            if (transform + 1000 < 0) {
                transform += 1000;
            } else {
                transform = 0;
            }
            dateList.style.transform = `translateX(${transform}px)`;
            bodyList.style.transform = `translateX(${transform}px)`;
            if (transform === 0) {
                arrowLeft.style.visibility = 'hidden';
            } else {
                arrowLeft.style.visibility = 'visible';
            }
            if (transform !== -2500) {
                arrowRight.style.visibility = 'visible';
            }
        }
        function moveRight() {
            arrowLeft.style.visibility = 'visible';
            if (transform - 1000 > -2500) {
                transform -= 1000;
            } else {
                transform = -2500;
            }
            dateList.style.transform = `translateX(${transform}px)`;
            bodyList.style.transform = `translateX(${transform}px)`;
            if (transform === -2500) {
                arrowRight.style.visibility = 'hidden';
            } else {
                arrowRight.style.visibility = 'visible';
            }
            if (transform !== 0) {
                arrowLeft.style.visibility = 'visible';
            }
        }
        arrowLeft.addEventListener('click', moveLeft);
        arrowRight.addEventListener('click', moveRight);
    }
}
    
 
// collection.html 

// 需要独立代码
// 用户输入的文字 安全化处理。。。。。。

// 修改清单详情
// if (location.pathname.substring(0,14) === "/subscribelist") {
    var LACY_POP_MC = {}
    var modifyCo = document.getElementsByClassName('co-md-txt')[0];
    var mcCancelBtn = document.getElementsByClassName('mc-can')[0];
    var mcConfirmBtn = document.getElementsByClassName('mc-con')[0];
    var mcClose = document.getElementsByClassName('mc-close-p')[0];
    var mcCover = document.querySelector('.mc-img>img');
    var mcCoverFile = document.querySelector('.mc-img input');
    var mcName = document.querySelector('.mc-name input');
    var mcSummery = document.querySelector('.mc-text textarea');

    var isOKmcName = true,
        isOKmcCover = true,
        isOKmcSummery = true;
     
    function modifyCollection(collectionId) {
       var popWin = document.getElementsByClassName('pop-up-window')[0];
       var mcWin = document.getElementsByClassName('modify-co')[0];
       popWin.style.visibility = 'visible';
       mcWin.style.visibility = 'visible';
       LACY_POP_MC.collectionId = collectionId;
    }

    function mcCancel() {
       var popWin = document.getElementsByClassName('pop-up-window')[0];
       var mcWin = document.getElementsByClassName('modify-co')[0];
       popWin.style.visibility = 'hidden';
       mcWin.style.visibility = 'hidden';
       mcName.value = '';
       mcSummery.value = '';
       mcCoverFile.value = '';
    }
    ///   检查图片并显示。 mc-warning

    function mcCofirm() {
        var popWin = document.getElementsByClassName('pop-up-window')[0];
        var mcWin = document.getElementsByClassName('modify-co')[0];

        if (!(isOKmcName && isOKmcSummery && isOKmcCover)) {
            return
        }
        if (!mcName.value && !mcSummery.value && mcCoverFile.value) {
            return
        }
        
        function uploadContextHandler() {
            var name = mcName.value;
            var summery = mcSummery.value;
                
            var pargams = {
                id: LACY_POP_MC.collectionId,
                name: name,
                summery: summery
            };
            var data = JSON.stringify(pargams);
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/j/collectionModify');
            xhr.setRequestHeader('Content-type', 'application/json');
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4 && xhr.status === 200) {
                    var response = JSON.parse(xhr.response);
                    if (!response) { 
                        infoPop('未知错误！');
                        return
                    }
                    if (response.code === 0) {
                        location.reload();
                    } else {
                        infoPop(response.message);
                    }
                }
            }
            xhr.send(data);
        }

        function uploadCoverHandler() {
            var f = new FormData();
            if (mcCoverFile.value) {
                f.append('file', mcCoverFile.files[0]);
                f.append('id', LACY_POP_MC.collectionId)
                var xhr = new XMLHttpRequest();
                xhr.open('POST', '/j/collectionModify');
                // xhr.setRequestHeader('Content-type', 'application/form-data');
                xhr.onreadystatechange = function() {
                    if (xhr.readyState === 4 && xhr.status === 200) {
                        var response = JSON.parse(xhr.response);
                        if (!response) { 
                            infoPop('未知错误！');
                            return
                        }
                        if (response.code === 0) {
                            location.reload();
                        } else {
                            infoPop(response.message);
                        }
                    }
                }
                xhr.send(f);
            }
        }
        uploadCoverHandler()
        uploadContextHandler()
    }
    mcClose.addEventListener('click', mcCancel);
    mcCancelBtn.addEventListener('click', mcCancel);
    mcConfirmBtn.addEventListener('click', mcCofirm);

    //

    // 检测字数，预览图片
    var mcWarning1 = document.querySelector('.mc-name p.mc-warning');
    var mcWarning2 = document.querySelector('.mc-text p.mc-warning');

    mcName.addEventListener('blur', function () {
        var v = mcName.value;
        if (v.length === 0) {
            mcWarning1.innerText = '';
            isOKmcName = true;
        } else if (v.length > 15) {
            mcWarning1.innerText = '超过15字';
            isOKmcName = false;
        } else {
            mcWarning1.innerText = '';
            isOKmcName = true;
        }
    });
    mcName.addEventListener('focus', function() {
        mcWarning1.innerText = '';
    })

    mcSummery.addEventListener('blur', function () {
        var v = mcSummery.value;
        if (v.length === 0) {
            mcWarning2.innerText = '';
            isOKmcSummery = true;
        } else if (v.length > 200) {
            mcWarning2.innerText = '超过200字';
            isOKmcSummery = false;
        } else {
            mcWarning1.innerText = '';
            isOKmcSummery = true;
        }
    });
    mcSummery.addEventListener('focus', function() {
        mcWarning2.innerText = '';
    })

    mcCoverFile.addEventListener('change', function() {
        if (!mcCoverFile.value) {
            infoPop('没有选择图片！');
            return;
        }
        var file = mcCoverFile.files[0];
        if (file.type !== 'image/jpg' && file.type !== 'image/png' && file.type !== 'image/gif') {
            infoPop('不是有效的图片文件！');
            isOKmcCover = false;
            return
        }

        var reader = new FileReader();
        reader.onload = function(e) {
            var data = e.target.result;
            mcCover.setAttribute('src', data);
        }
        reader.readAsDataURL(file);
        isOKmcCover = true;
    })
// }




// TV 选项

// 已看完 / 取消已看完
function setWatched(tvId) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/march/' + tvId);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var response = JSON.parse(xhr.response);
            if (!response) {
                infoPop('未知错误！');
                return
            }
            if (response.code === 0) {
                window.location.reload();
                infoPop('订阅成功！');
            } else {
                infoPop(response.message);
            }
        }
    }
    xhr.send();
}
function unsetWatched(tvId) {
    var xhr = new XMLHttpRequest();
    xhr.open('DELETE', '/march/' + tvId);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var response = JSON.parse(xhr.response);
            if (!response) {
                infoPop('未知错误！');
                return
            }
            if (response.code === 0) {
                window.location.reload();
                infoPop('操作成功！');
            } else {
                infoPop(response.message);
            }
        }
    }
    xhr.send();
}

// 信息提示框

function infoPop(msg) {
    var _body = $('body').first();
    var htmlContent = `
        <div class="head-msg fixed-top" id="info">
            <div class="alert alert-warning">
                ${msg}
            </div>
        </div>`;
    _body.append(htmlContent);
    var headMsg = $('.head-msg');
    headMsg.delay(3000).fadeOut();
    setTimeout(()=> headMsg.remove(), 3000);
}



// 追剧/取消追剧

function subscribeTV(tvId) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/subscribe/' + tvId);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var response = JSON.parse(xhr.response);
            if (!response) {
                infoPop('未知错误！');
                return
            }
            if (response.code === 0) {
                window.location.reload();
                infoPop('订阅成功！');
            } else {
                infoPop(response.message);
            }
        }
    }
    xhr.send();
}
function unsubscribeTV(tvId) {
    var xhr = new XMLHttpRequest();
    xhr.open('DELETE', '/subscribe/' + tvId);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var response = JSON.parse(xhr.response);
            if (!response) {
                infoPop('未知错误！');
                return
            }
            if (response.code === 0) {
                window.location.reload();
                infoPop('取消成功！');
            } else {
                infoPop(response.message);
            }
        }
    }
    xhr.send();
}

// tv_detail.html
// 收藏清单

function storeUpCollection(cId) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/storeUp/' + cId);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var response = JSON.parse(xhr.response);
            if (!response) {
                infoPop('未知错误！');
                return
            }
            if (response.code === 0) {
                window.location.reload();
                infoPop('收藏成功！');
            } else {
                infoPop(response.message);
            }
        }
    }
    xhr.send();
}
function unstoreUpCollection(cId) {
    var xhr = new XMLHttpRequest();
    xhr.open('DELETE', '/storeUp/' + cId);
    xhr.onreadystatechange = function() {
        if (xhr.readyState === 4 && xhr.status === 200) {
            var response = JSON.parse(xhr.response);
            if (!response) {
                infoPop('未知错误！');
                return
            }
            if (response.code === 0) {
                window.location.reload();
                infoPop('取消成功！');
            } else {
                infoPop(response.message);
            }
        }
    }
    xhr.send();
}