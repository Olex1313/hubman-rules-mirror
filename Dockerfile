# Используем официальный образа качестве родительского
FROM ubuntu

# Обновим систему
RUN apt-get update && apt-get upgrade -y

# Установим OpenSSH Server
RUN apt-get install -y openssh-server

# Настроим SSH
RUN mkdir /var/run/sshd
RUN echo 'root:Vova12092003' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# Исправление входа в систему SSH. В противном случае пользователя выкидывает из системы после входа
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile

#Открыть порт SSH
EXPOSE 22

# Запуск SSH
CMD ["/usr/sbin/sshd", "-D"]