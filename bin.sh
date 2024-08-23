#!/bin/bash

# 启用错误检测：脚本遇到错误时将立即退出
set -e

# 设置错误处理函数：当脚本遇到错误时执行
trap 'echo "错误发生！请检查 CloudFormation 和 CodeBuild 日志以获取详细信息。"; exit 1' ERR

# 显示重要提示信息
echo "
╔════════════════════════════ 重要提示 ════════════════════════════╗
║                                                                  ║
║         您正在运行多区域部署版本的 Research Assistant            ║
║                                                                  ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  • 如果您使用的是 v1.x 之前的版本（如 v0.4.x），请先查阅迁移指南 ║
║                                                                  ║
║  • 迁移过程需要特定步骤以确保数据正确保存和迁移                  ║
║                                                                  ║
║  • 请注意：不遵循迁移指南可能导致数据丢失                        ║
║                                                                  ║
║  • 迁移指南地址：                                                ║
║    https://github.com/ddipass/mutiple-region-ra                  ║
║                                                                  ║
║  • 新用户或已使用 v1.x 版本的用户可以安全继续安装                ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"

# 询问用户是否是新用户或 v1.x 用户
while true; do
    read -p "您是从 v1.x 或更高版本开始的新用户吗？ (y/N): " answer
    case ${answer:0:1} in
        y|Y )
            echo "开始部署..."
            break
            ;;
        n|N )
            echo "此脚本仅适用于新用户或 v1.x 用户。如果您使用的是之前的版本，请参阅迁移指南。"
            exit 1
            ;;
        * )
            echo "请输入 y 或 n。"
            ;;
    esac
done

# 设置默认参数
REGION="us-east-1"
ALLOW_SELF_REGISTER="true"
IPV4_RANGES=""
IPV6_RANGES=""
ALLOWED_SIGN_UP_EMAIL_DOMAINS='["gmail.com","amazon.com"]'
BEDROCK_REGION='{
  "claude-v3-sonnet": "us-east-1",
  "claude-v3.5-sonnet": "us-east-1",
  "claude-v3-opus": "us-west-2",
  "default": "us-west-2"
}'
GIT_BRANCH="main"
GIT_REPO="https://github.com/ddipass/mutiple-region-ra.git"
REPO_DIR="mutiple-region-ra"  

# 解析命令行参数以进行自定义设置
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --disable-self-register) ALLOW_SELF_REGISTER="false" ;;
        --ipv4-ranges) IPV4_RANGES="$2"; shift ;;
        --ipv6-ranges) IPV6_RANGES="$2"; shift ;;
        --region) REGION="$2"; shift ;;
        --allowed-signup-email-domains) ALLOWED_SIGN_UP_EMAIL_DOMAINS="$2"; shift ;;
        --git-branch) GIT_BRANCH="$2"; shift ;;
        --git-repo) GIT_REPO="$2"; shift ;;
        --repo-dir) REPO_DIR="$2"; shift ;;  
        *) echo "未知参数: $1"; exit 1 ;;
    esac
    shift
done

# 验证 CloudFormation 模板
echo "正在验证 CloudFormation 模板..."
aws cloudformation validate-template --template-body file://deploy.yml > /dev/null 2>&1
if [[ $? -ne 0 ]]; then
    echo "模板验证失败"
    exit 1
fi

# 设置 CloudFormation 堆栈名称
StackName="CodeBuildForDeploy"

# 部署 CloudFormation 堆栈
echo "正在部署 CloudFormation 堆栈..."
aws cloudformation deploy \
  --stack-name $StackName \
  --template-file deploy.yml \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    AllowSelfRegister=$ALLOW_SELF_REGISTER \
    Ipv4Ranges="$IPV4_RANGES" \
    Ipv6Ranges="$IPV6_RANGES" \
    AllowedSignUpEmailDomains="$ALLOWED_SIGN_UP_EMAIL_DOMAINS" \
    Region="$REGION" \
    ${BEDROCK_REGION:+"BedrockRegion=$BEDROCK_REGION"} \
    GitBranch="$GIT_BRANCH" \
    GitRepo="$GIT_REPO" \
    RepoDir="$REPO_DIR"

# 检查 CloudFormation 部署是否成功
if [ $? -ne 0 ]; then
    echo "CloudFormation 部署失败。正在获取错误详情..."
    aws cloudformation describe-stack-events --stack-name $StackName \
        --query 'StackEvents[?ResourceStatus==`CREATE_FAILED` || ResourceStatus==`UPDATE_FAILED`].[LogicalResourceId,ResourceStatusReason]' \
        --output table
    exit 1
fi

# 等待堆栈创建完成
echo "等待堆栈创建完成..."
echo "注意：此堆栈包含将用于 CDK 部署的 CodeBuild 项目。"

start_time=$(date +%s)
last_event_id=""

update_time() {
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))
    minutes=$((elapsed / 60))
    seconds=$((elapsed % 60))
    echo -ne "\r\033[K运行时间: ${minutes}分${seconds}秒 | "
}

while true; do
    update_time

    # 获取堆栈状态
    stack_info=$(aws cloudformation describe-stacks --stack-name $StackName 2>/dev/null)
    if [ $? -ne 0 ]; then
        echo "无法获取堆栈信息，请检查堆栈名称是否正确。"
        exit 1
    fi

    status=$(echo $stack_info | jq -r '.Stacks[0].StackStatus')

    # 获取最新的事件
    events=$(aws cloudformation describe-stack-events --stack-name $StackName --max-items 10)
    latest_event=$(echo "$events" | jq -r '.StackEvents[0]')
    latest_event_id=$(echo "$latest_event" | jq -r '.EventId')

    if [[ "$latest_event_id" != "$last_event_id" ]]; then
        resource_type=$(echo "$latest_event" | jq -r '.ResourceType')
        resource_status=$(echo "$latest_event" | jq -r '.ResourceStatus')
        echo -ne "$resource_type: $resource_status"
        last_event_id=$latest_event_id
    fi

    if [[ "$status" == "CREATE_COMPLETE" || "$status" == "UPDATE_COMPLETE" ]]; then
        echo -e "\n堆栈创建完成。"
        break
    elif [[ "$status" == "ROLLBACK_COMPLETE" || "$status" == "DELETE_FAILED" || "$status" == "CREATE_FAILED" ]]; then
        echo -e "\n堆栈创建失败，状态: $status"
        exit 1
    fi

    sleep 1
done

total_time=$(($(date +%s) - start_time))
total_minutes=$((total_time / 60))
total_seconds=$((total_time % 60))
echo "CloudFormation 部署总用时: ${total_minutes}分${total_seconds}秒"

# 获取 CodeBuild 项目名称
outputs=$(aws cloudformation describe-stacks --stack-name $StackName --query 'Stacks[0].Outputs')
projectName=$(echo $outputs | jq -r '.[] | select(.OutputKey=="ProjectName").OutputValue')

if [[ -z "$projectName" ]]; then
    echo "无法获取 CodeBuild 项目名称"
    exit 1
fi

# 启动 CodeBuild 项目
echo "正在启动 CodeBuild 项目: $projectName..."
buildId=$(aws codebuild start-build --project-name $projectName --query 'build.id' --output text)

if [[ -z "$buildId" ]]; then
    echo "启动 CodeBuild 项目失败"
    exit 1
fi

# 等待 CodeBuild 项目完成
echo "等待 CodeBuild 项目完成..."
codebuild_start_time=$(date +%s)
while true; do
    update_time
    buildStatus=$(aws codebuild batch-get-builds --ids $buildId --query 'builds[0].buildStatus' --output text)
    echo -ne "CodeBuild 状态: $buildStatus"
    if [[ "$buildStatus" == "SUCCEEDED" || "$buildStatus" == "FAILED" || "$buildStatus" == "STOPPED" ]]; then
        break
    fi
    sleep 5
done
echo -e "\nCodeBuild 项目完成，状态: $buildStatus"

codebuild_total_time=$(($(date +%s) - codebuild_start_time))
codebuild_minutes=$((codebuild_total_time / 60))
codebuild_seconds=$((codebuild_total_time % 60))
echo "CodeBuild 执行总用时: ${codebuild_minutes}分${codebuild_seconds}秒"

# 如果 CodeBuild 项目失败，获取并显示构建日志
if [ "$buildStatus" != "SUCCEEDED" ]; then
    echo "CodeBuild 项目失败。正在获取构建日志..."
    aws codebuild batch-get-builds --ids $buildId --query 'builds[0].logs' --output json
    exit 1
fi

# 获取构建日志详情
buildDetail=$(aws codebuild batch-get-builds --ids $buildId --query 'builds[0].logs.{groupName: groupName, streamName: streamName}' --output json)

logGroupName=$(echo $buildDetail | jq -r '.groupName')
logStreamName=$(echo $buildDetail | jq -r '.streamName')

echo "构建日志组名称: $logGroupName"
echo "构建日志流名称: $logStreamName"

# 获取 CDK 部署日志
echo "正在获取 CDK 部署日志..."
logs=$(aws logs get-log-events --log-group-name $logGroupName --log-stream-name $logStreamName)
frontendUrl=$(echo "$logs" | grep -o 'FrontendURL = [^ ]*' | cut -d' ' -f3 | tr -d '\n,')

echo "前端 URL: $frontendUrl"

# 显示部署完成信息
echo "部署成功完成。"
echo "CloudFormation 堆栈名称: $StackName"
echo "CodeBuild 项目名称: $projectName"
echo "CodeBuild 日志组: $logGroupName"
echo "CodeBuild 日志流: $logStreamName"
echo "要查看详细日志，请运行:"
echo "aws logs get-log-events --log-group-name $logGroupName --log-stream-name $logStreamName"

# 计算总运行时间
script_total_time=$(($(date +%s) - start_time))
script_total_minutes=$((script_total_time / 60))
script_total_seconds=$((script_total_time % 60))
echo "脚本总运行时间: ${script_total_minutes}分${script_total_seconds}秒"