// 全局变量
let currentPage = 1;
let totalPages = 1;
let isSearchMode = false;

document.addEventListener('DOMContentLoaded', () => {
    // 搜索模式切换
    document.getElementById('simpleSearchBtn').addEventListener('click', () => {
        document.getElementById('simpleSearchBtn').classList.add('active');
        document.getElementById('advancedSearchBtn').classList.remove('active');
        document.getElementById('simpleSearch').style.display = 'block';
        document.getElementById('advancedSearch').style.display = 'none';
    });
    
    document.getElementById('advancedSearchBtn').addEventListener('click', () => {
        document.getElementById('advancedSearchBtn').classList.add('active');
        document.getElementById('simpleSearchBtn').classList.remove('active');
        document.getElementById('simpleSearch').style.display = 'none';
        document.getElementById('advancedSearch').style.display = 'block';
    });

    // 搜索类型切换
    document.querySelectorAll('.search-type').forEach(card => {
        card.addEventListener('click', () => {
            // 移除所有激活状态
            document.querySelectorAll('.search-type').forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            // 更新描述文字
            const desc = document.getElementById('searchDesc');
            desc.textContent = card.dataset.type === 'exact' ? 
                '精确搜索：使用空格分隔关键词进行精准匹配' : 
                '示例：帮我总结一下法学院保研情况';
        });
    });

    // 高级搜索交互
    initAdvancedSearch();

    
    // 将performSearch设为全局函数
    window.performSearch = async function() {
        const searchType = document.querySelector('.search-type.active').dataset.type;
        const query = document.getElementById('searchInput').value.trim();
        
        if (!query) {
            window.showAllPosts();
            return;
        }
        
        isSearchMode = true;
        const resultsDiv = document.getElementById('results');
        const postsListDiv = document.getElementById('postsList');
        
        // 隐藏帖子列表，显示搜索结果
        postsListDiv.style.display = 'none';
        resultsDiv.style.display = 'block';
        resultsDiv.innerHTML = '<div class="text-center">搜索中...</div>';

        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    type: searchType,
                    query: searchType === 'exact' ? query.split(' ') : query,
                })
            });

            const data = await response.json();

            if (data.type === 'exact') {
                renderExactResults(data.results.posts);
            } else {
                renderAIResults(data.results);
            }
        } catch (error) {
            resultsDiv.innerHTML = `<div class="alert alert-danger">搜索失败：${error.message}</div>`;
        }
    };
    
    // 显示所有帖子
    window.showAllPosts = function() {
        isSearchMode = false;
        const resultsDiv = document.getElementById('results');
        const postsListDiv = document.getElementById('postsList');
        
        // 隐藏搜索结果，显示帖子列表
        resultsDiv.style.display = 'none';
        postsListDiv.style.display = 'block';
        
        // 重新加载第一页
        window.loadPosts(1);
    };
    
    // 搜索按钮点击
    document.getElementById('searchBtn').addEventListener('click', window.performSearch);
    
    // 回车键搜索
    document.getElementById('searchInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            window.performSearch();
        }
    });
    
    // 输入框变化时切换模式
    document.getElementById('searchInput').addEventListener('input', (e) => {
        if (e.target.value.trim() === '') {
            // 输入框为空时显示所有帖子
            window.showAllPosts();
        }
    });
    
    // 加载帖子列表
    window.loadPosts = async function(page) {
        try {
            const response = await fetch(`/posts?page=${page}&per_page=20`);
            const data = await response.json();
            
            if (data.error) {
                document.getElementById('postsContainer').innerHTML = 
                    `<div class="alert alert-warning">${data.error}</div>`;
                return;
            }
            
            currentPage = data.page;
            totalPages = data.total_pages;
            
            // 更新分页信息
            document.getElementById('paginationInfo').textContent = 
                `第 ${currentPage} 页，共 ${totalPages} 页，总计 ${data.total} 条帖子`;
            
            // 渲染帖子
            renderPosts(data.posts);
            
            // 渲染分页
            renderPagination();
            
        } catch (error) {
            document.getElementById('postsContainer').innerHTML = 
                `<div class="alert alert-danger">加载失败：${error.message}</div>`;
        }
    };
    
    // 渲染帖子列表
    function renderPosts(posts) {
        const container = document.getElementById('postsContainer');
        
        if (posts.length === 0) {
            container.innerHTML = '<div class="alert alert-info">暂无帖子</div>';
            return;
        }
        
        const html = posts.map(post => `
            <div class="post-card mb-3">
                <div class="card">
                    <div class="card-body post-content-area" ${post.comment_count > 0 ? `onclick="toggleComments(${post.id}, this)"` : ''} style="${post.comment_count > 0 ? 'cursor: pointer;' : ''}">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <h6 class="card-title mb-0">#${post.id}</h6>
                            <div class="text-muted small">
                                <span class="badge bg-secondary me-1">${post.class_name}</span>
                                <span>${post.time}</span>
                            </div>
                        </div>
                        <p class="card-text">${escapeHtml(post.content)}</p>
                        <div class="d-flex justify-content-between align-items-center">
                            <div class="text-muted small">
                                <span class="me-3">👍 ${post.good_count}</span>
                                <span>💬 ${post.comment_count}</span>
                            </div>
                            ${post.comment_count > 0 ? 
                                `<span class="text-primary small">
                                    <i class="fas fa-comments"></i> 点击查看评论 (${post.comment_count})
                                </span>` : 
                                '<span class="text-muted small">暂无评论</span>'
                            }
                        </div>
                        <div id="comments-${post.id}" class="comments-section mt-3" style="display: none;">
                            <div class="text-center">
                                <div class="spinner-border spinner-border-sm" role="status">
                                    <span class="visually-hidden">加载中...</span>
                                </div>
                                <span class="ms-2">加载评论中...</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
        
        container.innerHTML = html;
    }
    
    // 渲染分页
    function renderPagination() {
        const pagination = document.getElementById('pagination');
        
        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }
        
        let html = '';
        
        // 上一页
        if (currentPage > 1) {
            html += `<li class="page-item">
                <a class="page-link" href="#" onclick="loadPosts(${currentPage - 1})">上一页</a>
            </li>`;
        }
        
        // 页码
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            html += `<li class="page-item ${i === currentPage ? 'active' : ''}">
                <a class="page-link" href="#" onclick="loadPosts(${i})">${i}</a>
            </li>`;
        }
        
        // 下一页
        if (currentPage < totalPages) {
            html += `<li class="page-item">
                <a class="page-link" href="#" onclick="loadPosts(${currentPage + 1})">下一页</a>
            </li>`;
        }
        
        pagination.innerHTML = html;
    }
    
    // 将loadPosts设为全局函数
    window.loadPosts = loadPosts;
    
    // 切换评论显示
    window.toggleComments = async function(postId, element) {
        const commentsSection = document.getElementById(`comments-${postId}`);
        
        if (!commentsSection) {
            console.error('Comments section not found for postId:', postId);
            return;
        }
        
        const isHidden = commentsSection.style.display === 'none' || commentsSection.style.display === '';
        
        if (isHidden) {
            // 显示评论
            commentsSection.style.display = 'block';
            
            // 更新提示文本
            const hintElement = element.querySelector('.text-primary');
            if (hintElement) {
                hintElement.innerHTML = '<i class="fas fa-comments"></i> 点击收起评论';
            }
            
            // 如果还没有加载过评论，则加载
            if (commentsSection.innerHTML.includes('加载评论中')) {
                await loadComments(postId);
            }
        } else {
            // 隐藏评论
            commentsSection.style.display = 'none';
            
            // 更新提示文本
            const hintElement = element.querySelector('.text-primary');
            if (hintElement) {
                const commentCount = hintElement.textContent.match(/\d+/)?.[0] || '0';
                hintElement.innerHTML = `<i class="fas fa-comments"></i> 点击查看评论 (${commentCount})`;
            }
        }
    };
    
    // 加载评论
    async function loadComments(postId) {
        const commentsSection = document.getElementById(`comments-${postId}`);
        
        try {
            const response = await fetch(`/post/${postId}/comments`);
            const data = await response.json();
            
            if (data.error) {
                commentsSection.innerHTML = `<div class="alert alert-warning">${data.error}</div>`;
                return;
            }
            
            if (data.comments.length === 0) {
                commentsSection.innerHTML = '<div class="text-muted text-center">暂无评论</div>';
                return;
            }
            
            // 渲染评论
            const commentsHtml = data.comments.map(comment => `
                <div class="comment-item border-start border-3 border-light ps-3 mb-3">
                    <div class="d-flex justify-content-between align-items-start mb-1">
                        <h6 class="comment-id mb-0">#${comment.id}</h6>
                        <div class="text-muted small">
                            <span class="badge bg-light text-dark me-1">${comment.class_name}</span>
                            <span>${comment.time}</span>
                        </div>
                    </div>
                    <p class="comment-content mb-2">${escapeHtml(comment.content)}</p>
                    <div class="text-muted small">
                        <span class="me-3">👍 ${comment.good_count}</span>
                        <span>💬 ${comment.comment_count}</span>
                    </div>
                </div>
            `).join('');
            
            commentsSection.innerHTML = `
                <div class="comments-header mb-3">
                    <h6 class="text-muted">评论列表 (${data.comments.length}条)</h6>
                </div>
                ${commentsHtml}
            `;
            
    } catch (error) {
        commentsSection.innerHTML = `<div class="alert alert-danger">加载评论失败：${error.message}</div>`;
    }
}

// 高级搜索初始化
function initAdvancedSearch() {
    // 下拉菜单切换
    document.querySelectorAll('.sort-default').forEach(defaultEl => {
        defaultEl.addEventListener('click', (e) => {
            e.stopPropagation();
            const sortList = defaultEl.nextElementSibling;
            if (sortList && sortList.classList.contains('sort-list')) {
                // 关闭其他下拉菜单
                document.querySelectorAll('.sort-list').forEach(list => {
                    if (list !== sortList) {
                        list.style.display = 'none';
                    }
                });
                // 切换当前下拉菜单
                sortList.style.display = sortList.style.display === 'none' ? 'block' : 'none';
            }
        });
    });

    // 下拉菜单选项点击
    document.querySelectorAll('.sort-list a').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const li = link.parentElement;
            const sortList = li.parentElement;
            const defaultEl = sortList.previousElementSibling;
            const span = defaultEl.querySelector('span');
            
            // 更新显示文本
            span.textContent = link.textContent;
            span.setAttribute('value', link.getAttribute('value'));
            
            // 更新选中状态
            sortList.querySelectorAll('li').forEach(item => item.classList.remove('cur'));
            li.classList.add('cur');
            
            // 关闭下拉菜单
            sortList.style.display = 'none';
        });
    });

    // 添加搜索条件
    document.querySelectorAll('.add-group').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            addSearchCondition();
        });
    });

    // 删除搜索条件
    document.querySelectorAll('.del-group').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const dd = btn.closest('dd');
            if (dd && document.querySelectorAll('#gradetxt dd').length > 1) {
                dd.remove();
            }
        });
    });

    // 高级搜索按钮 - 使用事件委托
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn-search') || e.target.value === '检索') {
            e.preventDefault();
            performAdvancedSearch();
        }
        if (e.target.classList.contains('btn-reset')) {
            e.preventDefault();
            resetAdvancedSearch();
        }
    });

    // 快速时间选择
    document.querySelectorAll('.tit-dropdown-box .sort-list a').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const value = link.getAttribute('value');
            const today = new Date();
            let startDate = '';
            let endDate = today.toISOString().split('T')[0];
            
            if (value === 'recent_week') {
                const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
                startDate = weekAgo.toISOString().split('T')[0];
            } else if (value === 'recent_month') {
                const monthAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000);
                startDate = monthAgo.toISOString().split('T')[0];
            } else if (value === 'recent_quarter') {
                const quarterAgo = new Date(today.getTime() - 90 * 24 * 60 * 60 * 1000);
                startDate = quarterAgo.toISOString().split('T')[0];
            } else if (value === 'recent_year') {
                const yearAgo = new Date(today.getTime() - 365 * 24 * 60 * 60 * 1000);
                startDate = yearAgo.toISOString().split('T')[0];
            }
            
            if (value && value !== '') {
                document.getElementById('datebox0').value = startDate;
                document.getElementById('datebox1').value = endDate;
            } else {
                document.getElementById('datebox0').value = '';
                document.getElementById('datebox1').value = '';
            }
            
            // 更新显示文本
            const defaultEl = link.closest('.sort-list').previousElementSibling;
            const span = defaultEl.querySelector('span');
            span.textContent = link.textContent;
            span.setAttribute('value', value);
            
            // 更新选中状态
            link.closest('.sort-list').querySelectorAll('li').forEach(item => item.classList.remove('cur'));
            link.parentElement.classList.add('cur');
            
            // 关闭下拉菜单
            link.closest('.sort-list').style.display = 'none';
        });
    });

    // 点击其他地方关闭下拉菜单
    document.addEventListener('click', () => {
        document.querySelectorAll('.sort-list').forEach(list => {
            list.style.display = 'none';
        });
    });
}

// 添加搜索条件
function addSearchCondition() {
    const inputsList = document.getElementById('gradetxt');
    const maxCount = parseInt(inputsList.dataset.maxlen) || 10;
    const currentCount = inputsList.querySelectorAll('dd').length;
    
    if (currentCount >= maxCount) {
        alert(`最多只能添加${maxCount}个搜索条件`);
        return;
    }

    const newDd = document.createElement('dd');
    newDd.innerHTML = `
        <div class="sort logical">
            <div class="sort-default">
                <span value="AND">AND</span>
                <em>∨</em>
            </div>
            <ul class="sort-list">
                <li class="cur"><a href="javascript:void(0);" value="AND">AND</a></li>
                <li><a href="javascript:void(0);" value="OR">OR</a></li>
                <li><a href="javascript:void(0);" value="NOT">NOT</a></li>
            </ul>
        </div>
        <div class="input-box">
            <div class="sort reopt">
                <div class="sort-default">
                    <span value="FT" data-opter="TOPRANK" data-value="FT">全文</span>
                    <i class="icon-sort">▼</i>
                </div>
                <div class="sort-list" style="display: none;">
                    <ul>
                        <li data-val="FT" class="cur">
                            <a value="BOTH" data-opt="TOPRANK" data-advdefault="DEFAULT" title="全文">全文</a>
                        </li>
                        <li data-val="SU">
                            <a value="DEFAULT" data-opt="TOPRANK" data-advdefault="DEFAULT" title="主题">主题</a>
                        </li>
                    </ul>
                </div>
            </div>
            <input type="text" autocomplete="off" maxlength="120" placeholder="输入搜索内容">
            <div class="sort special">
                <div class="sort-default">
                    <span value="=">精确</span>
                    <em>∨</em>
                </div>
                <ul class="sort-list" mode="BOTH">
                    <li class="cur"><a value="=">精确</a></li>
                    <li><a value="%">模糊</a></li>
                </ul>
            </div>
        </div>
        <a class="icon-btn del-group" href="javascript:void(0)">-</a>
    `;

    // 插入到最后一个dd之前
    const lastDd = inputsList.querySelector('dd:last-of-type');
    lastDd.parentNode.insertBefore(newDd, lastDd);

    // 重新绑定事件
    initAdvancedSearch();
}

// 执行高级搜索
function performAdvancedSearch() {
    const searchConditions = [];
    const inputsList = document.getElementById('gradetxt');
    
    if (!inputsList) {
        console.error('高级搜索容器未找到');
        return;
    }
    
    inputsList.querySelectorAll('dd').forEach((dd, index) => {
        // 安全地获取各个元素
        const logicalElement = dd.querySelector('.logical .sort-default span');
        const fieldElement = dd.querySelector('.reopt .sort-default span');
        const valueElement = dd.querySelector('input[type="text"]');
        const matchElement = dd.querySelector('.special .sort-default span');
        
        // 检查元素是否存在
        if (!logicalElement || !fieldElement || !valueElement || !matchElement) {
            console.warn(`第${index + 1}个搜索条件元素不完整，跳过`);
            return;
        }
        
        const logical = logicalElement.getAttribute('value');
        const field = fieldElement.getAttribute('value');
        const value = valueElement.value.trim();
        const match = matchElement.getAttribute('value');
        
        if (value) {
            if (index === 0) {
                // 第一个条件不需要逻辑运算符
                searchConditions.push(value);
            } else {
                // 根据逻辑运算符和匹配模式构建条件
                if (logical === 'AND') {
                    searchConditions.push(value);
                } else if (logical === 'OR') {
                    searchConditions.push(`OR ${value}`);
                } else if (logical === 'NOT') {
                    searchConditions.push(`NOT ${value}`);
                }
            }
        }
    });

    if (searchConditions.length === 0) {
        // 没有搜索条件时，显示所有帖子
        window.showAllPosts();
        return;
    }

    // 获取时间范围
    const startDate = document.getElementById('datebox0').value;
    const endDate = document.getElementById('datebox1').value;
    
    // 构建搜索查询
    let query = searchConditions.join(' ');
    
    // 添加时间范围
    if (startDate && endDate) {
        query += ` 时间:${startDate}到${endDate}`;
    } else if (startDate) {
        query += ` 时间:${startDate}起`;
    } else if (endDate) {
        query += ` 时间:${endDate}前`;
    }

    // 执行搜索
    document.getElementById('searchInput').value = query;
    window.performSearch();
}

// 重置高级搜索
function resetAdvancedSearch() {
    // 重置所有输入框
    document.querySelectorAll('#gradetxt input[type="text"]').forEach(input => {
        input.value = '';
    });
    
    // 重置下拉菜单到默认值
    document.querySelectorAll('#gradetxt .sort-default span').forEach(span => {
        if (span.closest('.logical')) {
            span.textContent = 'AND';
            span.setAttribute('value', 'AND');
        } else if (span.closest('.reopt')) {
            span.textContent = '全文';
            span.setAttribute('value', 'FT');
        } else if (span.closest('.special')) {
            span.textContent = '精确';
            span.setAttribute('value', '=');
        }
    });
    
    // 重置时间范围
    document.getElementById('datebox0').value = '';
    document.getElementById('datebox1').value = '';
    
    // 重置快速选择
    const quickSelect = document.querySelector('.tit-dropdown-box .sort-default span');
    if (quickSelect) {
        quickSelect.textContent = '不限';
        quickSelect.setAttribute('value', '');
    }
    
    // 只保留第一个搜索条件
    const inputsList = document.getElementById('gradetxt');
    const dds = inputsList.querySelectorAll('dd');
    for (let i = 1; i < dds.length; i++) {
        dds[i].remove();
    }
}



    function renderAIResults(markdown) {
        document.getElementById('results').innerHTML = `
            <div class="ai-results p-3 bg-light rounded">
                ${marked.parse(markdown)}
            </div>
        `;
    }
    
    // 初始加载所有帖子
    window.loadPosts(1);
});

// 全局函数用于切换评论显示
let currentPosts = [];
let currentKeywords = [];

function highlightKeywords(text, keywords) {
    if (!keywords || keywords.length === 0) return text;
    keywords.forEach(keyword => {
        if (keyword.trim() === '') return;
        const escaped = keyword.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        const regex = new RegExp(escaped, 'gi');
        text = text.replace(regex, match => `<mark>${match}</mark>`);
    });
    return text;
}

function escapeRegExp(string) {
    return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}



// 新增过滤和排序函数
function filterByDate() {
    const start = document.getElementById('startDate').value;
    const end = document.getElementById('endDate').value;
    
    const filtered = currentPosts.filter(post => {
        const postDate = post.post_date.replace(/-/g, '');
        const startDate = start.replace(/-/g, '');
        const endDate = end.replace(/-/g, '');
        return (!start || postDate >= startDate) && (!end || postDate <= endDate);
    });
    
    renderExactResults(filtered);
}

function sortPosts() {
    const sortBy = document.getElementById('sortSelect').value;
    const sorted = [...currentPosts];
    
    sorted.sort((a, b) => {
        if (sortBy === 'date') {
            return b.post_date.localeCompare(a.post_date);
        } else {
            const hotA = a.good_count + a.comment_count;
            const hotB = b.good_count + b.comment_count;
            return hotB - hotA;
        }
    });
    
    renderExactResults(sorted);
}

// 修改performSearch函数保存当前结果
// 搜索结果分页相关变量
let searchCurrentPage = 1;
let searchTotalPages = 1;
let searchPostsPerPage = 20;
let allSearchPosts = [];

// 在renderExactResults函数中
function renderExactResults(posts) {
    allSearchPosts = posts;
    searchTotalPages = Math.ceil(posts.length / searchPostsPerPage);
    searchCurrentPage = 1;
    
    renderSearchResultsPage(1);
}

// 渲染搜索结果页面
function renderSearchResultsPage(page) {
    searchCurrentPage = page;
    const startIndex = (page - 1) * searchPostsPerPage;
    const endIndex = startIndex + searchPostsPerPage;
    const pagePosts = allSearchPosts.slice(startIndex, endIndex);
    
    const html = `
        <div class="d-flex justify-content-between align-items-center mb-3">
            <div class="sort-control">
                <select id="sortSelect" class="form-select" onchange="sortSearchPosts(this.value)">
                    <option value="time">最新排序</option>
                    <option value="hot">热度排序</option>
                </select>
            </div>
            <div class="search-pagination-info">
                第 ${page} 页，共 ${searchTotalPages} 页，共 ${allSearchPosts.length} 条结果
            </div>
        </div>
        ${pagePosts.map(post => `
            <div class="post-card position-relative">
                <div class="post-header" onclick="toggleComments(${post.id}, this)">
                    <h4 class="post-title">#${post.id}</h4>
                    <div class="post-meta">
                        <span class="post-time">${post.post_time || ''}</span>
                        ${post.comment_count > 0 ? 
                            `<span class="comment-count-badge">${post.comment_count}条评论</span>` : 
                            '<span class="comment-count-badge">暂无评论</span>'
                        }
                    </div>
                </div>
                <div class="post-content">${post.content}</div>
                ${post.comment_count > 0 ? 
                    `<div id="comments-${post.id}" class="comments-section mt-3" style="display: none;">
                        <div class="text-center">
                            <div class="spinner-border spinner-border-sm" role="status">
                                <span class="visually-hidden">加载中...</span>
                            </div>
                            <span class="ms-2">加载评论中...</span>
                        </div>
                    </div>` : ''
                }
            </div>
        `).join('')}
        ${renderSearchPagination()}
    `;
    
    const resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = html;
}

// 渲染搜索结果分页
function renderSearchPagination() {
    if (searchTotalPages <= 1) return '';
    
    let paginationHtml = '<nav aria-label="搜索结果分页" class="mt-4"><ul class="pagination justify-content-center">';
    
    // 上一页
    if (searchCurrentPage > 1) {
        paginationHtml += `<li class="page-item">
            <a class="page-link" href="javascript:void(0)" onclick="renderSearchResultsPage(${searchCurrentPage - 1})">上一页</a>
        </li>`;
    }
    
    // 页码
    const startPage = Math.max(1, searchCurrentPage - 2);
    const endPage = Math.min(searchTotalPages, searchCurrentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        paginationHtml += `<li class="page-item ${i === searchCurrentPage ? 'active' : ''}">
            <a class="page-link" href="javascript:void(0)" onclick="renderSearchResultsPage(${i})">${i}</a>
        </li>`;
    }
    
    // 下一页
    if (searchCurrentPage < searchTotalPages) {
        paginationHtml += `<li class="page-item">
            <a class="page-link" href="javascript:void(0)" onclick="renderSearchResultsPage(${searchCurrentPage + 1})">下一页</a>
        </li>`;
    }
    
    paginationHtml += '</ul></nav>';
    return paginationHtml;
}

// 新增排序函数
function sortSearchPosts(type) {
    const sortedPosts = [...allSearchPosts].sort((a, b) => {
        if (type === 'hot') {
            return b.comment_count - a.comment_count;
        } else {
            return new Date(b.post_time) - new Date(a.post_time);
        }
    });
    
    allSearchPosts = sortedPosts;
    renderSearchResultsPage(1);
}
// function renderExactResults(posts) {
//     const html = posts.map(post => `
//         <div class="post-card position-relative" onclick="toggleComments(this)">
//             <div class="post-content">${post.content}</div>
//             <div class="comment-count">${post.comments.length}条评论</div>
//             <div class="comments">
//                 ${post.comments.map(comment => `
//                     <div class="comment-item">
//                         ${comment.content}
//                     </div>
//                 `).join('')}
//             </div>
//         </div>
//     `).join('');
//     document.getElementById('results').innerHTML = html;
// }

// function toggleComments(element) {
//     const commentsDiv = element.querySelector('.comments');
//     commentsDiv.style.display = commentsDiv.style.display === 'none' ? 'block' : 'none';
    
//     // 添加展开/收起动画
//     if (commentsDiv.style.display === 'block') {
//         element.classList.add('active');
//     } else {
//         element.classList.remove('active');
//     }
// }
// 添加在文件末尾
function submitFeedback() {
    const feedback = document.getElementById('feedbackInput').value;
    if (!feedback.trim()) {
        alert('请输入反馈内容');
        return;
    }

    fetch('/feedback', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ feedback: feedback })
    })
    .then(response => {
        if (response.ok) {
            alert('反馈提交成功！');
            bootstrap.Modal.getInstance(document.getElementById('feedbackModal')).hide();
        } else {
            throw new Error('提交失败');
        }
    })
    .catch(error => {
        alert('提交失败，请稍后再试');
    });
}