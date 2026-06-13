FROM python:3.10-slim

USER root
ENV HOME=/root

RUN apt-get update && apt-get install -y \
    curl \
    git \
    unzip \
    xz-utils \
    zip \
    sudo \
    && rm -rf /var/lib/apt/lists/*

ENV J_HOST=download.java.net
ENV J_PATH=java/GA/jdk17.0.2/dfd4a8d0985749f896bed50d7138ee7f/8/GPL
ENV J_FILE=openjdk-17.0.2_linux-x64_bin.tar.gz

ENV A_HOST=dl.google.com
ENV A_PATH=android/repository
ENV A_FILE=commandlinetools-linux-11076708_latest.zip

RUN mkdir -p /opt/java \
    && curl -L -o /tmp/openjdk.tar.gz https://${J_HOST}/${J_PATH}/${J_FILE} \
    && tar -xf /tmp/openjdk.tar.gz -C /opt/java --strip-components=1 \
    && rm /tmp/openjdk.tar.gz

ENV JAVA_HOME=/opt/java
ENV ANDROID_HOME=/opt/android-sdk
ENV PATH=$PATH:$JAVA_HOME/bin:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools:$ANDROID_HOME/build-tools;34.0.0

RUN mkdir -p $ANDROID_HOME/cmdline-tools \
    && curl -L -o /tmp/cmdline.zip https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip \
    && unzip -q /tmp/cmdline.zip -d $ANDROID_HOME/cmdline-tools \
    && mv $ANDROID_HOME/cmdline-tools/cmdline-tools $ANDROID_HOME/cmdline-tools/latest \
    && rm /tmp/cmdline.zip

RUN yes | sdkmanager --licenses
RUN sdkmanager "platform-tools" "platforms;android-34" "build-tools;34.0.0"

RUN chmod -R 777 /opt

WORKDIR $HOME/app

COPY requirements.txt $HOME/app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r $HOME/app/requirements.txt

COPY . $HOME/app

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-7860}"]
