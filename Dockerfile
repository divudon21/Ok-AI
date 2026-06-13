FROM python:3.10-slim

# Force system to run as root explicitly
USER root
ENV HOME=/root

# Basic tools download karein
RUN apt-get update && apt-get install -y \
    curl \
    git \
    unzip \
    xz-utils \
    zip \
    sudo \
    && rm -rf /var/lib/apt/lists/*

# URL ko puri tarah obfuscate kar diya taaki web parser ise link na banaye
ENV J_HOST=download.java.net
ENV J_PATH=java/GA/jdk17.0.2/dfd4a8d0985749f896bed50d7138ee7f/8/GPL
ENV J_FILE=openjdk-17.0.2_linux-x64_bin.tar.gz

# Android Repo Obfuscation
ENV A_HOST=dl.google.com
ENV A_PATH=android/repository
ENV A_FILE=commandlinetools-linux-11076708_latest.zip

# Production-ready OpenJDK 17 Linux x64 Binary download aur extract karein
RUN mkdir -p /opt/java \
    && curl -L -o /tmp/openjdk.tar.gz https://${J_HOST}/${J_PATH}/${J_FILE} \
    && tar -xf /tmp/openjdk.tar.gz -C /opt/java --strip-components=1 \
    && rm /tmp/openjdk.tar.gz

# Environment variables set karein taaki Java aur Android globally accessible ho
ENV JAVA_HOME=/opt/java
ENV ANDROID_HOME=/opt/android-sdk
ENV PATH=$PATH:$JAVA_HOME/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/build-tools/34.0.0

# Android Command Line Tools setup
RUN mkdir -p $ANDROID_HOME/cmdline-tools \
    && curl -L -o /tmp/cmdline.zip https://${A_HOST}/${A_PATH}/${A_FILE} \
    && unzip -q /tmp/cmdline.zip -d $ANDROID_HOME/cmdline-tools \
    && mv $ANDROID_HOME/cmdline-tools/cmdline-tools $ANDROID_HOME/cmdline-tools/latest \
    && rm /tmp/cmdline.zip

# Non-interactive licenses accept karein
RUN yes | sdkmanager --licenses

# Android SDK Platforms aur Build Tools pehle se load kar rahe hain
RUN sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"

# Pre-install global standalone Gradle binaries inside sandbox to enable local wrapper instantiation
RUN mkdir -p /opt/gradle \
    && curl -L -o /tmp/gradle.zip https://services.gradle.org/distributions/gradle-7.5.1-bin.zip \
    && unzip -q /tmp/gradle.zip -d /opt/gradle \
    && rm /tmp/gradle.zip
ENV PATH=$PATH:/opt/gradle/gradle-7.5.1/bin

# Permissions 777 root core systems ke liye
RUN chmod -R 777 /opt

WORKDIR $HOME/app

COPY requirements.txt $HOME/app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r $HOME/app/requirements.txt

COPY . $HOME/app

# Fixed for Render: Binding dynamically to Render assigned network port to prevent request routing errors
CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-7860}"]
