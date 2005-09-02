#include <stdio.h>
#include <string.h>
#include <stdlib.h>

char *
gftp_descramble_password (const char *password)
{
  const char *passwordpos;
  char *newstr, *newpos;
  int error;

  if (*password != '$') return strdup (password);

  passwordpos = password + 1;
  newstr = malloc(strlen (passwordpos) / 2 + 1);
  newpos = newstr;
 
  error = 0;
  while (*passwordpos != '\0' && (*passwordpos + 1) != '\0')
    {
      if ((*passwordpos & 0xc3) != 0x41 ||
          (*(passwordpos + 1) & 0xc3) != 0x41)
        {
          error = 1;
          break;
        }

      *newpos++ = ((*passwordpos & 0x3c) << 2) | 
                  ((*(passwordpos + 1) & 0x3c) >> 2);

      passwordpos += 2;
    }

  if (error)
    {
      free (newstr);
      return (strdup (password));
    }

  *newpos = '\0';
  return (newstr);
}

int main(int argc, char **argv)
{
  if (argc != 2) {
    fprintf(stderr, "Need one argument : gftp crambled password.\n");
    return 1;
  }
  char *txt = gftp_descramble_password(argv[1]);
  printf ("%s", txt);
  return 0;
}
