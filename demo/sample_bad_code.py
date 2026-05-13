"""
这是一个有各种问题的示例代码，用于演示代码审查工具的能力
这段代码故意包含安全漏洞、性能问题和规范问题
"""
import os
import subprocess
import pickle
import hashlib
import requests


# ========== 安全问题 ==========

# 硬编码密钥
api_key = "sk-1234567890abcdefghijklmnopqrstuvwxyz"
password = "admin123456"
SECRET_TOKEN = "my_secret_token_abc"

def run_command(user_input):
    # 命令注入风险
    os.system("ping " + user_input)
    subprocess.call("ls " + user_input, shell=True)

def execute_user_code(code):
    # 任意代码执行
    result = eval(code)
    exec(code)
    return result

def load_data(filepath):
    with open(filepath, "rb") as f:
        # 不安全的反序列化
        data = pickle.load(f)
    return data

def hash_password(pwd):
    # 弱哈希算法
    return hashlib.md5(pwd.encode()).hexdigest()

def fetch_api(url):
    # 禁用SSL验证
    resp = requests.get(url, verify=False)
    return resp.json()


# ========== 性能问题 ==========

def find_duplicates(items):
    # 嵌套循环 O(n^2)
    duplicates = []
    for i in range(len(items)):
        for j in range(len(items)):
            if i != j and items[i] == items[j]:
                duplicates.append(items[i])
    return duplicates

def build_report(data_list):
    # 循环内字符串拼接
    report = ""
    for item in data_list:
        report = report + str(item) + "\n"
        report = report + "=" * 50 + "\n"
    return report

def process_all_items(items, config, cache, logger, validator, formatter, dispatcher, tracker, monitor, auditor, reporter, analyzer, compressor, encryptor, decryptor, router, balancer, fallback, circuit_breaker, rate_limiter, timeout_handler, retry_policy, backoff_strategy, jitter_handler, health_checker, metrics_collector, alert_manager, log_aggregator, trace_exporter, span_recorder, baggage_handler, context_propagator, sampler, resource_detector, attribute_extractor, event_processor, link_processor, status_processor, error_handler, success_handler, warning_handler, info_handler, debug_handler, trace_handler, fatal_handler, critical_handler, notice_handler, emergency_handler, alert_handler, audit_handler, compliance_handler, security_handler, privacy_handler, gdpr_handler, ccpa_handler, hipaa_handler, pci_handler, sox_handler, iso_handler, nist_handler, cis_handler):
    # 超长函数 - 超过50行
    result = []
    if not items:
        logger.warning("empty input")
        return result

    cache_key = hash_password(str(items))
    if cache_key in cache:
        logger.info("cache hit")
        return cache[cache_key]

    for idx, item in enumerate(items):
        if not validator.validate(item):
            logger.error(f"invalid item at {idx}")
            continue

        formatted = formatter.format(item)
        if formatted is None:
            continue

        processed = dispatcher.dispatch(formatted)
        tracker.track(processed)
        monitor.observe(processed)

        if auditor.audit(processed):
            result.append(processed)
            reporter.report(processed)
            analyzer.analyze(processed)

        compressed = compressor.compress(processed)
        encrypted = encryptor.encrypt(compressed)
        routed = router.route(encrypted)
        balanced = balancer.balance(routed)

        if circuit_breaker.is_open():
            fallback.execute(balanced)
        else:
            try:
                rate_limiter.acquire()
                timeout_handler.execute(balanced)
                result.append(balanced)
            except Exception as e:
                retry_policy.retry(balanced, e)

        health_checker.check()
        metrics_collector.collect()
        alert_manager.evaluate()
        log_aggregator.aggregate()
        trace_exporter.export()

        if idx % 100 == 0:
            context_propagator.propagate()
            sampler.sample(processed)

    cache[cache_key] = result
    return result


# ========== 规范问题 ==========

def calculate_price(quantity):
    # 嵌套太深 + 魔法数字
    if quantity > 0:
        if quantity < 10:
            if quantity < 5:
                if quantity < 3:
                    if quantity == 1:
                        return 9.99
                    return 8.99
                return 7.99
            return 6.99
        else:
            if quantity < 100:
                if quantity < 50:
                    return 5.99
                return 4.99
            else:
                return 3.99
    return 0

def long_function_name_that_does_way_too_many_things_in_one_single_function_and_should_definitely_be_refactored_into_smaller_pieces(data):
    # 过长的行
    result = [item for sublist in data for item in sublist if item is not None and isinstance(item, (int, float, str)) and len(str(item)) > 0 and str(item).strip() != "" and not str(item).startswith("_")]
    return result
