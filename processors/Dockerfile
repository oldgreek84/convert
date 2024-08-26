# Use a minimal Debian Bookworm Slim base image
FROM debian:bookworm-slim

# Set environment variables to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies, Python, Calibre, and libfontconfig
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    python3 \
    python3-pip \
    xz-utils \
    ca-certificates \
    libgl1-mesa-glx \
    libdbus-1-3 \
    libfontconfig1 \
    libegl1 \
    libopengl0 \
    libxcb-cursor0 \
    libqt5gui5 \
    && wget -nv -O- https://download.calibre-ebook.com/linux-installer.sh | sh /dev/stdin \
    && apt-get purge --auto-remove -y wget xz-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Set the necessary environment variables for Calibre
ENV PATH="/opt/calibre/bin:$PATH"
ENV LD_LIBRARY_PATH="/opt/calibre/lib:$LD_LIBRARY_PATH"

# Set the working directory
WORKDIR /mnt/books

# Set the default command to bash, allowing interactive sessions
CMD ["bash"]
